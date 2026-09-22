"""
Integration tests proving the end-to-end ML pipeline:
Database records -> feature_service.extract_ml_features() -> prediction_service.predict_final_score()

Validates:
1. Semester 1 end-to-end extraction and inference.
2. Semesters 2+ end-to-end extraction and inference.
3. Model dispatching to the respective trained .joblib artifacts.
4. Feature contract compatibility (direct dictionary pass-through without modifications).
5. Strict CT2 and FINAL exclusion (ensuring CT2/FINAL additions do not alter features or predictions).
6. Model artifact metadata alignment with the fixed ML contract.
"""

import math
import sys
import unittest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure app imports resolve cleanly
sys.path.insert(0, "backend")

from app.base import Base
# Register all SQLAlchemy model tables
import app.models.user
import app.models.department
import app.models.course
import app.models.faculty
import app.models.student
import app.models.subject
import app.models.enrollment
import app.models.attendance
import app.models.assessment

from app.models.course import Course
from app.models.student import Student
from app.models.subject import Subject
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assessment import Assessment, AssessmentType
from app.services.feature_service import extract_ml_features
from app.services.prediction_service import (
    predict_final_score,
    get_model_metadata,
    get_model_artifact_path,
)


class TestFeaturePredictionIntegration(unittest.TestCase):
    """End-to-end integration tests connecting feature extraction to ML prediction."""

    def setUp(self):
        """Set up an isolated in-memory SQLite database for each test."""
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
    # TEST 1 — SEMESTER 1 END-TO-END
    # ==================================================================

    def test_01_semester_1_end_to_end_pipeline(self):
        """
        Verify complete inference pipeline for Semester 1:
        DB records -> extract_ml_features(semester=1) -> predict_final_score(semester=1).
        Verify prediction succeeds, is numeric, finite, not None, without feature-order errors.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1, name="CS101")

        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)

        # Attendance: 4 PRESENT, 1 ABSENT -> 80.0%
        for i in range(1, 5):
            self._create_attendance(attendance_id=i, enrollment_id=1, status=AttendanceStatus.PRESENT, day=i)
        self._create_attendance(attendance_id=5, enrollment_id=1, status=AttendanceStatus.ABSENT, day=5)

        # Assignment: 18 / 20 -> 90.0%
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment 1",
            max_marks=20,
            obtained_marks=18,
        )

        # CT1: 17 / 20 -> 85.0%
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="Class Test 1",
            max_marks=20,
            obtained_marks=17,
        )

        # Extract features
        features = extract_ml_features(self.db, student_id=1, semester=1)

        # Verify exact feature dictionary keys
        expected_keys = {
            "current_attendance",
            "current_assignment_average",
            "current_ct1_average",
        }
        self.assertEqual(set(features.keys()), expected_keys)
        self.assertEqual(features["current_attendance"], 80.0)
        self.assertEqual(features["current_assignment_average"], 90.0)
        self.assertEqual(features["current_ct1_average"], 85.0)

        # Pass directly into prediction_service
        prediction = predict_final_score(semester=1, features=features)

        # Assert prediction properties
        self.assertIsNotNone(prediction)
        self.assertIsInstance(prediction, float)
        self.assertTrue(math.isfinite(prediction))
        # Ensure prediction is a reasonable final semester score
        self.assertGreater(prediction, 0.0)
        self.assertLess(prediction, 120.0)

    # ==================================================================
    # TEST 2 — SEMESTERS 2+ END-TO-END
    # ==================================================================

    def test_02_semesters_2_to_4_end_to_end_pipeline(self):
        """
        Verify complete inference pipeline for Semesters 2+:
        DB records -> extract_ml_features(semester=2) -> predict_final_score(semester=2).
        Verify prediction succeeds, is numeric, finite, not None, without feature-order errors.
        """
        self._create_student(student_id=2, current_semester=2)

        # --- Semester 1 (Previous Semester) ---
        self._create_subject(subject_id=101, semester=1, name="Sem1 Subject")
        self._create_enrollment(
            enrollment_id=1,
            student_id=2,
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
        # Previous academic result: 82 / 100 -> 82.0%
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Sem1 Final Exam",
            max_marks=100,
            obtained_marks=82,
        )

        # --- Semester 2 (Target Current Semester) ---
        self._create_subject(subject_id=201, semester=2, name="Sem2 Subject")
        self._create_enrollment(
            enrollment_id=2,
            student_id=2,
            subject_id=201,
            status=EnrollmentStatus.ENROLLED,
        )
        # Current attendance: 4 PRESENT, 1 ABSENT -> 80.0%
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
        # Current assignment: 40 / 50 -> 80.0%
        self._create_assessment(
            assessment_id=2,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Sem2 Assignment 1",
            max_marks=50,
            obtained_marks=40,
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

        # Extract features for semester 2
        features = extract_ml_features(self.db, student_id=2, semester=2)

        # Verify exact feature dictionary keys
        expected_keys = {
            "previous_semester_score",
            "previous_semester_attendance",
            "current_attendance",
            "current_assignment_average",
            "current_ct1_average",
        }
        self.assertEqual(set(features.keys()), expected_keys)
        self.assertEqual(features["previous_semester_score"], 82.0)
        self.assertEqual(features["previous_semester_attendance"], 100.0)
        self.assertEqual(features["current_attendance"], 80.0)
        self.assertEqual(features["current_assignment_average"], 80.0)
        self.assertEqual(features["current_ct1_average"], 75.0)

        # Pass directly into prediction_service
        prediction = predict_final_score(semester=2, features=features)

        # Assert prediction properties
        self.assertIsNotNone(prediction)
        self.assertIsInstance(prediction, float)
        self.assertTrue(math.isfinite(prediction))
        self.assertGreater(prediction, 0.0)
        self.assertLess(prediction, 120.0)

    # ==================================================================
    # TEST 3 — MODEL DISPATCHING
    # ==================================================================

    def test_03_model_dispatching_resolves_correct_artifacts(self):
        """
        Verify that:
        - semester=1 uses 'vcis_model_semester1.joblib'
        - semester=2, 3, 4 uses 'vcis_model_semesters2_4.joblib'
        Checked via get_model_artifact_path and get_model_metadata.
        """
        path_s1 = get_model_artifact_path(1)
        self.assertTrue(path_s1.name.endswith("vcis_model_semester1.joblib"))
        self.assertTrue(path_s1.is_file(), f"Artifact missing: {path_s1}")

        for sem in (2, 3, 4):
            path_sem = get_model_artifact_path(sem)
            self.assertTrue(path_sem.name.endswith("vcis_model_semesters2_4.joblib"))
            self.assertTrue(path_sem.is_file(), f"Artifact missing for semester {sem}: {path_sem}")

        meta1 = get_model_metadata(1)
        self.assertEqual(meta1["scenario"], "Semester 1")
        self.assertEqual(len(meta1["feature_names"]), 3)

        for sem in (2, 3, 4):
            meta_sem = get_model_metadata(sem)
            self.assertEqual(meta_sem["scenario"], "Semesters 2+")
            self.assertEqual(len(meta_sem["feature_names"]), 5)

    # ==================================================================
    # TEST 4 — FEATURE CONTRACT COMPATIBILITY
    # ==================================================================

    def test_04_direct_dictionary_pass_through_without_alteration(self):
        """
        Verify that the dictionary returned by extract_ml_features can be passed
        directly to predict_final_score WITHOUT any dictionary alteration, re-ordering,
        or metadata stripping.
        """
        self._create_student(student_id=3, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=3, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=16,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=14,
        )

        extracted_dict = extract_ml_features(self.db, student_id=3, semester=1)

        # Directly pass the dictionary object without reordering, copying, or modifying
        prediction = predict_final_score(semester=1, features=extracted_dict)
        self.assertIsInstance(prediction, float)
        self.assertTrue(math.isfinite(prediction))

    # ==================================================================
    # TEST 5 — CT2 AND FINAL DO NOT AFFECT CURRENT FEATURES OR PREDICTION
    # ==================================================================

    def test_05_ct2_and_final_do_not_leak_into_features_or_predictions(self):
        """
        Prove that adding CT2 and FINAL assessment records with extreme values
        does NOT alter the extracted features OR the resulting prediction.
        """
        self._create_student(student_id=4, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=4, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst 1",
            max_marks=20,
            obtained_marks=18,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1 1",
            max_marks=20,
            obtained_marks=16,
        )

        # 1. Baseline extraction & prediction
        features_before = extract_ml_features(self.db, student_id=4, semester=1)
        prediction_before = predict_final_score(semester=1, features=features_before)

        # 2. Add extreme CT2 (0 marks) and extreme FINAL (0 marks)
        self._create_assessment(
            assessment_id=3,
            enrollment_id=1,
            assessment_type=AssessmentType.CT2,
            assessment_name="CT2 Extreme",
            max_marks=20,
            obtained_marks=0,
        )
        self._create_assessment(
            assessment_id=4,
            enrollment_id=1,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Final Exam Extreme",
            max_marks=100,
            obtained_marks=0,
        )

        # 3. Extraction & prediction after adding CT2 and FINAL
        features_after = extract_ml_features(self.db, student_id=4, semester=1)
        prediction_after = predict_final_score(semester=1, features=features_after)

        # Strict invariant assertion: exact equality
        self.assertEqual(features_before, features_after)
        self.assertEqual(prediction_before, prediction_after)

    # ==================================================================
    # TEST 6 — MODEL ARTIFACT METADATA
    # ==================================================================

    def test_06_model_artifact_metadata_matches_fixed_contract(self):
        """
        Verify that both trained model artifacts maintain exact consistency
        with the fixed VCIS ML contract.
        """
        # --- Semester 1 Model ---
        meta1 = get_model_metadata(1)
        self.assertEqual(
            meta1["feature_names"],
            [
                "current_attendance",
                "current_assignment_average",
                "current_ct1_average",
            ],
        )
        self.assertEqual(meta1["target_name"], "final_semester_score")
        self.assertEqual(meta1["model_type"], "LinearRegression")
        self.assertEqual(meta1["scenario"], "Semester 1")

        # --- Semesters 2+ Model ---
        meta2 = get_model_metadata(2)
        self.assertEqual(
            meta2["feature_names"],
            [
                "previous_semester_score",
                "previous_semester_attendance",
                "current_attendance",
                "current_assignment_average",
                "current_ct1_average",
            ],
        )
        self.assertEqual(meta2["target_name"], "final_semester_score")
        self.assertEqual(meta2["model_type"], "LinearRegression")
        self.assertEqual(meta2["scenario"], "Semesters 2+")


if __name__ == "__main__":
    unittest.main()
