"""
Automated tests for VCIS 3.0 ML Feature Extraction Service (feature_service.py).

Validates the fixed VCIS ML contract:
- Model 1 (Semester 1): current_attendance, current_assignment_average, current_ct1_average
- Model 2 (Semesters 2+): previous_semester_score, previous_semester_attendance,
                           current_attendance, current_assignment_average, current_ct1_average
- Strict exclusions: student_id, semester, final_semester_score, CT2, FINAL, INTERNAL
- Missing data safety: InsufficientDataError (no zero-filling/fabrication)
- Structural CT1 identification via AssessmentType.CT1
- Status filtering: dropped enrollments excluded
- Semester resolution via Subject.semester
"""

import sys
import unittest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure app imports resolve cleanly
sys.path.insert(0, "backend")

from app.base import Base
# Import all model modules to register table metadata
import app.models.user
import app.models.department
import app.models.course
import app.models.faculty
import app.models.student
import app.models.subject
import app.models.enrollment
import app.models.attendance
import app.models.assessment

from app.models.student import Student
from app.models.subject import Subject
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.course import Course
from app.models.student import Student
from app.models.subject import Subject
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assessment import Assessment, AssessmentType
from app.services.feature_service import (
    extract_semester_1_features,
    extract_semesters_2_plus_features,
    extract_semesters_2_to_4_features,
    extract_ml_features,
    InsufficientDataError,
    UnsupportedSemesterError,
    StudentNotFoundError,
)


class TestFeatureService(unittest.TestCase):
    """Test suite validating exact student-semester ML feature extraction."""

    def setUp(self):
        """Create an isolated in-memory SQLite database for each test."""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()

    def tearDown(self):
        """Clean up the isolated database session."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    # ------------------------------------------------------------------
    # Helper Fixture Creators
    # ------------------------------------------------------------------

    def _create_student(
        self,
        student_id: int = 1,
        current_semester: int = 1,
        course_id: int = 1,
        total_semesters: int = 4,
    ) -> Student:
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if course is None:
            course = Course(
                id=course_id,
                department_id=1,
                name="MCA" if course_id == 1 else f"Course {course_id}",
                code="MCA" if course_id == 1 else f"CRS{course_id}",
                duration_years=2 if total_semesters <= 4 else 4,
                total_semesters=total_semesters,
                is_active=True,
            )
            self.db.add(course)
            self.db.commit()

        student = Student(
            id=student_id,
            user_id=student_id,
            department_id=1,
            course_id=course_id,
            roll_number=f"ROLL_{student_id}",
            admission_year=2024,
            current_semester=current_semester,
            name=f"Student {student_id}",
            email=f"student{student_id}@test.com",
            is_active=True,
        )
        self.db.add(student)
        self.db.commit()
        return student

    def _create_subject(self, subject_id: int, semester: int, name: str = "Subject") -> Subject:
        subject = Subject(
            id=subject_id,
            course_id=1,
            name=f"{name} {subject_id}",
            code=f"SUB_{subject_id}",
            semester=semester,
            credits=4,
            is_active=True,
        )
        self.db.add(subject)
        self.db.commit()
        return subject

    def _create_enrollment(
        self,
        enrollment_id: int,
        student_id: int,
        subject_id: int,
        status: EnrollmentStatus = EnrollmentStatus.ENROLLED,
    ) -> Enrollment:
        enrollment = Enrollment(
            id=enrollment_id,
            student_id=student_id,
            subject_id=subject_id,
            academic_year="2024-25",
            status=status,
        )
        self.db.add(enrollment)
        self.db.commit()
        return enrollment

    def _create_attendance(
        self,
        attendance_id: int,
        enrollment_id: int,
        status: AttendanceStatus,
        day: int = 1,
    ) -> Attendance:
        record = Attendance(
            id=attendance_id,
            enrollment_id=enrollment_id,
            attendance_date=date(2024, 9, day),
            status=status,
        )
        self.db.add(record)
        self.db.commit()
        return record

    def _create_assessment(
        self,
        assessment_id: int,
        enrollment_id: int,
        assessment_type: AssessmentType,
        assessment_name: str,
        max_marks: int,
        obtained_marks: int,
    ) -> Assessment:
        record = Assessment(
            id=assessment_id,
            enrollment_id=enrollment_id,
            assessment_type=assessment_type,
            assessment_name=assessment_name,
            max_marks=max_marks,
            obtained_marks=obtained_marks,
            assessment_date=date(2024, 9, 15),
        )
        self.db.add(record)
        self.db.commit()
        return record

    # ==================================================================
    # TEST 1 — SEMESTER 1 FEATURE VECTOR
    # ==================================================================

    def test_01_semester_1_feature_vector_exact_calculation(self):
        """
        Verify extract_semester_1_features returns exactly:
        - current_attendance = (PRESENT / total) * 100
        - current_assignment_average = arithmetic mean of assignment percentages
        - current_ct1_average = arithmetic mean of CT1 percentages
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1, name="Prog")
        self._create_subject(subject_id=102, semester=1, name="Math")

        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)
        self._create_enrollment(enrollment_id=2, student_id=1, subject_id=102)

        # Attendance: 3 PRESENT, 1 ABSENT -> 3/4 * 100 = 75.0%
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT, day=1)
        self._create_attendance(attendance_id=2, enrollment_id=1, status=AttendanceStatus.PRESENT, day=2)
        self._create_attendance(attendance_id=3, enrollment_id=2, status=AttendanceStatus.PRESENT, day=3)
        self._create_attendance(attendance_id=4, enrollment_id=2, status=AttendanceStatus.ABSENT, day=4)

        # Assignments:
        # A1: 18 / 20 = 90.0%
        # A2: 40 / 50 = 80.0%
        # Average: (90 + 80) / 2 = 85.0%
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment 1",
            max_marks=20,
            obtained_marks=18,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment 2",
            max_marks=50,
            obtained_marks=40,
        )

        # CT1s:
        # CT1_1: 16 / 20 = 80.0%
        # CT1_2: 18 / 20 = 90.0%
        # Average: (80 + 90) / 2 = 85.0%
        self._create_assessment(
            assessment_id=3,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="Class Test 1 - Prog",
            max_marks=20,
            obtained_marks=16,
        )
        self._create_assessment(
            assessment_id=4,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="Class Test 1 - Math",
            max_marks=20,
            obtained_marks=18,
        )

        features = extract_semester_1_features(self.db, student_id=1)

        self.assertEqual(
            features,
            {
                "current_attendance": 75.0,
                "current_assignment_average": 85.0,
                "current_ct1_average": 85.0,
            },
        )

    # ==================================================================
    # TEST 2 — SEMESTERS 2+ FEATURE VECTOR
    # ==================================================================

    def test_02_semesters_2_to_4_feature_vector_exact_calculation(self):
        """
        Verify extract_semesters_2_to_4_features returns exactly 5 features:
        - previous_semester_score (from semester target_semester - 1)
        - previous_semester_attendance (from semester target_semester - 1)
        - current_attendance (from current semester)
        - current_assignment_average (from current semester)
        - current_ct1_average (from current semester)
        """
        self._create_student(student_id=1, current_semester=2)

        # --- Semester 1 (Previous Semester) ---
        self._create_subject(subject_id=101, semester=1, name="Sem1 Subject")
        self._create_enrollment(
            enrollment_id=1,
            student_id=1,
            subject_id=101,
            status=EnrollmentStatus.COMPLETED,
        )
        # Previous attendance: 4 PRESENT, 0 ABSENT -> 100.0%
        for i in range(1, 5):
            self._create_attendance(
                attendance_id=i,
                enrollment_id=1,
                status=AttendanceStatus.PRESENT,
                day=i,
            )
        # Previous academic performance: 85 / 100 -> 85.0%
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Sem1 Final Exam",
            max_marks=100,
            obtained_marks=85,
        )

        # --- Semester 2 (Target Current Semester) ---
        self._create_subject(subject_id=201, semester=2, name="Sem2 Subject")
        self._create_enrollment(
            enrollment_id=2,
            student_id=1,
            subject_id=201,
            status=EnrollmentStatus.ENROLLED,
        )
        # Current attendance: 4 PRESENT, 1 ABSENT -> 4/5 * 100 = 80.0%
        for i in range(5, 9):
            self._create_attendance(
                attendance_id=i,
                enrollment_id=2,
                status=AttendanceStatus.PRESENT,
                day=i,
            )
        self._create_attendance(
            attendance_id=9,
            enrollment_id=2,
            status=AttendanceStatus.ABSENT,
            day=9,
        )
        # Current assignment: 45 / 50 -> 90.0%
        self._create_assessment(
            assessment_id=2,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Sem2 Assignment 1",
            max_marks=50,
            obtained_marks=45,
        )
        # Current CT1: 15 / 20 -> 75.0%
        self._create_assessment(
            assessment_id=3,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="Sem2 CT1",
            max_marks=20,
            obtained_marks=15,
        )

        features = extract_semesters_2_to_4_features(self.db, student_id=1, semester=2)

        self.assertEqual(
            features,
            {
                "previous_semester_score": 85.0,
                "previous_semester_attendance": 100.0,
                "current_attendance": 80.0,
                "current_assignment_average": 90.0,
                "current_ct1_average": 75.0,
            },
        )

    # ==================================================================
    # TEST 3 — CT2 EXCLUSION
    # ==================================================================

    def test_03_ct2_exclusion_from_features(self):
        """
        Verify that AssessmentType.CT2 records are completely excluded from
        current_ct1_average and do not pollute the feature vector.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)

        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)

        # CT1: 10 / 20 = 50.0%
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="Class Test 1",
            max_marks=20,
            obtained_marks=10,
        )
        # CT2: 20 / 20 = 100.0% (MUST NOT BE INCLUDED)
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT2,
            assessment_name="Class Test 2",
            max_marks=20,
            obtained_marks=20,
        )
        # Assignment: 20 / 20 = 100.0%
        self._create_assessment(
            assessment_id=3,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment 1",
            max_marks=20,
            obtained_marks=20,
        )

        features = extract_semester_1_features(self.db, student_id=1)

        # If CT2 had been included, average would be (50 + 100)/2 = 75.0%
        # It must strictly be 50.0%
        self.assertEqual(features["current_ct1_average"], 50.0)

    # ==================================================================
    # TEST 4 — FINAL EXCLUSION
    # ==================================================================

    def test_04_final_assessment_exclusion(self):
        """
        Verify that AssessmentType.FINAL in the current semester has zero effect
        on current_attendance, current_assignment_average, or current_ct1_average.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)

        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)

        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="Class Test 1",
            max_marks=20,
            obtained_marks=16,  # 80.0%
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment 1",
            max_marks=20,
            obtained_marks=18,  # 90.0%
        )
        # FINAL exam record with radically different score
        self._create_assessment(
            assessment_id=3,
            enrollment_id=1,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Semester Final Exam",
            max_marks=100,
            obtained_marks=10,  # 10.0%
        )

        features = extract_semester_1_features(self.db, student_id=1)

        self.assertEqual(features["current_attendance"], 100.0)
        self.assertEqual(features["current_assignment_average"], 90.0)
        self.assertEqual(features["current_ct1_average"], 80.0)

    # ==================================================================
    # TEST 5 — INTERNAL EXCLUSION
    # ==================================================================

    def test_05_internal_assessment_exclusion(self):
        """
        Verify that AssessmentType.INTERNAL is excluded from current_ct1_average
        even if its assessment_name resembles 'Class Test 1'.
        CT1 must be identified strictly via AssessmentType.CT1.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)

        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)

        # True structural CT1: 14 / 20 = 70.0%
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="Actual CT1",
            max_marks=20,
            obtained_marks=14,
        )
        # Legacy/generic INTERNAL named 'Class Test 1': 20 / 20 = 100.0%
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.INTERNAL,
            assessment_name="Class Test 1 - Internal",
            max_marks=20,
            obtained_marks=20,
        )
        self._create_assessment(
            assessment_id=3,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment 1",
            max_marks=20,
            obtained_marks=18,
        )

        features = extract_semester_1_features(self.db, student_id=1)

        # Must strictly reflect CT1 (70.0%), ignoring INTERNAL (100.0%)
        self.assertEqual(features["current_ct1_average"], 70.0)

    # ==================================================================
    # TEST 6 — STUDENT_ID IS NOT A FEATURE
    # ==================================================================

    def test_06_metadata_and_forbidden_fields_not_in_features(self):
        """
        Verify that student_id, semester, final_semester_score, and previous_semester_gpa
        are never included in the extracted ML feature dictionary.
        """
        self._create_student(student_id=42, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=42, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment",
            max_marks=20,
            obtained_marks=18,
        )

        features = extract_semester_1_features(self.db, student_id=42)

        forbidden_keys = {
            "student_id",
            "semester",
            "final_semester_score",
            "previous_semester_gpa",
            "gpa",
            "id",
        }
        for key in forbidden_keys:
            self.assertNotIn(key, features)

    # ==================================================================
    # TEST 7 — EXACT FEATURE KEYS
    # ==================================================================

    def test_07_exact_feature_keys_semester_1_and_semesters_2_to_4(self):
        """
        Verify exact dictionary keys returned:
        - Semester 1: exactly {"current_attendance", "current_assignment_average", "current_ct1_average"}
        - Semesters 2+: exactly {"previous_semester_score", "previous_semester_attendance",
                                  "current_attendance", "current_assignment_average", "current_ct1_average"}
        """
        self._create_student(student_id=1, current_semester=2)

        # Sem 1 setup
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101, status=EnrollmentStatus.COMPLETED)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Final",
            max_marks=100,
            obtained_marks=80,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )
        self._create_assessment(
            assessment_id=3,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=18,
        )

        # Sem 2 setup
        self._create_subject(subject_id=201, semester=2)
        self._create_enrollment(enrollment_id=2, student_id=1, subject_id=201, status=EnrollmentStatus.ENROLLED)
        self._create_attendance(attendance_id=2, enrollment_id=2, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=4,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )
        self._create_assessment(
            assessment_id=5,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=18,
        )

        # Test Sem 1 keys
        features_s1 = extract_semester_1_features(self.db, student_id=1)
        self.assertEqual(
            set(features_s1.keys()),
            {
                "current_attendance",
                "current_assignment_average",
                "current_ct1_average",
            },
        )

        # Test Sem 2 keys
        features_s2 = extract_semesters_2_to_4_features(self.db, student_id=1, semester=2)
        self.assertEqual(
            set(features_s2.keys()),
            {
                "previous_semester_score",
                "previous_semester_attendance",
                "current_attendance",
                "current_assignment_average",
                "current_ct1_average",
            },
        )

    # ==================================================================
    # TEST 8 — UNSUPPORTED SEMESTERS
    # ==================================================================

    def test_08_unsupported_semesters_raise_error(self):
        """
        Verify that semesters outside 1–4 (such as 0, 5, -1, 6) raise
        UnsupportedSemesterError in extract_semesters_2_to_4_features and extract_ml_features.
        """
        self._create_student(student_id=1, current_semester=1)

        unsupported = [0, 5, -1, 6, 10]
        for sem in unsupported:
            with self.assertRaises(UnsupportedSemesterError):
                extract_semesters_2_to_4_features(self.db, student_id=1, semester=sem)

            with self.assertRaises(UnsupportedSemesterError):
                extract_ml_features(self.db, student_id=1, semester=sem)

        # Calling extract_semesters_2_to_4_features with semester 1 is also unsupported (Model 1 applies to Sem 1)
        with self.assertRaises(UnsupportedSemesterError):
            extract_semesters_2_to_4_features(self.db, student_id=1, semester=1)

    # ==================================================================
    # TEST 9 — MISSING REQUIRED DATA
    # ==================================================================

    def test_09_missing_required_data_raises_insufficient_data_error(self):
        """
        Verify InsufficientDataError is raised when any required data is missing:
        - Missing attendance
        - Missing assignments
        - Missing CT1
        - Missing previous semester score
        - Missing previous semester attendance
        Values must not be silently zero-filled.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)

        # 1. Missing attendance records
        with self.assertRaises(InsufficientDataError) as ctx:
            extract_semester_1_features(self.db, student_id=1)
        self.assertIn("attendance", str(ctx.exception).lower())

        # Add attendance
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)

        # 2. Missing assignments
        with self.assertRaises(InsufficientDataError) as ctx:
            extract_semester_1_features(self.db, student_id=1)
        self.assertIn("assignment", str(ctx.exception).lower())

        # Add assignment
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst 1",
            max_marks=20,
            obtained_marks=18,
        )

        # 3. Missing CT1
        with self.assertRaises(InsufficientDataError) as ctx:
            extract_semester_1_features(self.db, student_id=1)
        self.assertIn("ct1", str(ctx.exception).lower())

        # Now add CT1 to make Semester 1 complete
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )

        # 4. Now test Semester 2 with missing previous semester completed result
        self._create_subject(subject_id=201, semester=2)
        self._create_enrollment(enrollment_id=2, student_id=1, subject_id=201)
        self._create_attendance(attendance_id=2, enrollment_id=2, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=3,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst 2",
            max_marks=20,
            obtained_marks=18,
        )
        self._create_assessment(
            assessment_id=4,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1 Sem2",
            max_marks=20,
            obtained_marks=16,
        )

        # Previous semester has no completed result (no final/graded assessments total_max_marks > 0 in sem 1
        # because sem 1 only has 20 + 20 max marks and no final)
        # Wait, get_student_semester_result returns overall_percentage for sem 1 if total_max_marks > 0.
        # Let's delete enrollment 1 to make previous semester completely missing:
        self.db.query(Attendance).filter(Attendance.enrollment_id == 1).delete()
        self.db.query(Assessment).filter(Assessment.enrollment_id == 1).delete()
        self.db.query(Enrollment).filter(Enrollment.id == 1).delete()
        self.db.commit()

        with self.assertRaises(InsufficientDataError) as ctx:
            extract_semesters_2_to_4_features(self.db, student_id=1, semester=2)
        self.assertIn("previous_semester", str(ctx.exception).lower())

    # ==================================================================
    # TEST 10 — MAX MARKS VALIDATION
    # ==================================================================

    def test_10_max_marks_less_or_equal_zero_raises_error(self):
        """
        Verify that an assessment with max_marks <= 0 raises InsufficientDataError.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)

        # Invalid assignment record with max_marks = 0
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Faulty Assignment",
            max_marks=0,
            obtained_marks=0,
        )

        with self.assertRaises(InsufficientDataError) as ctx:
            extract_semester_1_features(self.db, student_id=1)
        self.assertIn("max_marks", str(ctx.exception).lower())

    # ==================================================================
    # TEST 11 — DROPPED ENROLLMENTS
    # ==================================================================

    def test_11_dropped_enrollments_are_excluded(self):
        """
        Verify that enrollments with EnrollmentStatus.DROPPED are excluded from
        all feature calculations.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1, name="Active Subject")
        self._create_subject(subject_id=102, semester=1, name="Dropped Subject")

        # Active enrollment: 1 PRESENT class, 100% attendance, perfect scores
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101, status=EnrollmentStatus.ENROLLED)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=20,  # 100.0%
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=20,  # 100.0%
        )

        # Dropped enrollment: 10 ABSENT classes, 0 marks (must be ignored)
        self._create_enrollment(enrollment_id=2, student_id=1, subject_id=102, status=EnrollmentStatus.DROPPED)
        for i in range(2, 12):
            self._create_attendance(attendance_id=i, enrollment_id=2, status=AttendanceStatus.ABSENT, day=i)
        self._create_assessment(
            assessment_id=3,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Dropped Asst",
            max_marks=20,
            obtained_marks=0,
        )
        self._create_assessment(
            assessment_id=4,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="Dropped CT1",
            max_marks=20,
            obtained_marks=0,
        )

        features = extract_semester_1_features(self.db, student_id=1)

        # If dropped enrollment was included, attendance would be 1/11 ~ 9.09% and scores 50.0%
        # Must be 100.0% across all features:
        self.assertEqual(features["current_attendance"], 100.0)
        self.assertEqual(features["current_assignment_average"], 100.0)
        self.assertEqual(features["current_ct1_average"], 100.0)

    # ==================================================================
    # TEST 12 — SEMESTER RESOLUTION
    # ==================================================================

    def test_12_semester_resolved_via_subject_semester(self):
        """
        Verify that Subject.semester determines which semester an enrollment belongs to,
        ensuring cross-semester data is not contaminated.
        """
        self._create_student(student_id=1, current_semester=1)
        # Subject A is semester 1, Subject B is semester 2
        self._create_subject(subject_id=101, semester=1, name="Sem1 Subject")
        self._create_subject(subject_id=201, semester=2, name="Sem2 Subject")

        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)
        self._create_enrollment(enrollment_id=2, student_id=1, subject_id=201)

        # Sem 1 attendance: 1 PRESENT (100.0%)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        # Sem 2 attendance: 10 ABSENT (0.0%)
        for i in range(2, 12):
            self._create_attendance(attendance_id=i, enrollment_id=2, status=AttendanceStatus.ABSENT, day=i)

        # Sem 1 assessments: 80% CT1, 90% Assignment
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1 Sem1",
            max_marks=20,
            obtained_marks=16,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst Sem1",
            max_marks=20,
            obtained_marks=18,
        )

        # Sem 2 assessments with different marks
        self._create_assessment(
            assessment_id=3,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1 Sem2",
            max_marks=20,
            obtained_marks=2,
        )
        self._create_assessment(
            assessment_id=4,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst Sem2",
            max_marks=20,
            obtained_marks=2,
        )

        features = extract_semester_1_features(self.db, student_id=1)

        # Must strictly reflect Subject.semester == 1
        self.assertEqual(features["current_attendance"], 100.0)
        self.assertEqual(features["current_assignment_average"], 90.0)
        self.assertEqual(features["current_ct1_average"], 80.0)

    # ==================================================================
    # TEST 13 — DISPATCHER
    # ==================================================================

    def test_13_dispatcher_extract_ml_features(self):
        """
        Verify extract_ml_features correctly routes:
        - semester=1 -> 3 features (Model 1)
        - semester=2, 3, 4 -> 5 features (Model 2)
        - semester=None -> uses student.current_semester
        - invalid semester -> raises UnsupportedSemesterError
        - non-existent student -> raises StudentNotFoundError
        """
        self._create_student(student_id=1, current_semester=1)

        # Setup sem 1
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101, status=EnrollmentStatus.COMPLETED)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=18,
        )

        # Setup sem 2
        self._create_subject(subject_id=201, semester=2)
        self._create_enrollment(enrollment_id=2, student_id=1, subject_id=201, status=EnrollmentStatus.COMPLETED)
        self._create_attendance(attendance_id=2, enrollment_id=2, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=3,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )
        self._create_assessment(
            assessment_id=4,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=18,
        )

        # 1. Dispatch with semester=1 -> Model 1 (3 features)
        res_1 = extract_ml_features(self.db, student_id=1, semester=1)
        self.assertEqual(len(res_1), 3)
        self.assertIn("current_attendance", res_1)

        # 2. Dispatch with semester=None -> uses student.current_semester (which is 1)
        res_default = extract_ml_features(self.db, student_id=1, semester=None)
        self.assertEqual(res_1, res_default)

        # 3. Dispatch with semester=2 -> Model 2 (5 features)
        res_2 = extract_ml_features(self.db, student_id=1, semester=2)
        self.assertEqual(len(res_2), 5)
        self.assertIn("previous_semester_score", res_2)

        # 4. Dispatch with unsupported semesters
        with self.assertRaises(UnsupportedSemesterError):
            extract_ml_features(self.db, student_id=1, semester=0)

        with self.assertRaises(UnsupportedSemesterError):
            extract_ml_features(self.db, student_id=1, semester=5)

        # 5. Dispatch with non-existent student
        with self.assertRaises(StudentNotFoundError):
            extract_ml_features(self.db, student_id=99999, semester=1)


if __name__ == "__main__":
    unittest.main()
