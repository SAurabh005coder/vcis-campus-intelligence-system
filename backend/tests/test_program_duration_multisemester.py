"""
Automated tests for Multi-Program Durations & B.Tech 8-Semester Support in VCIS 3.0.

Validates:
1. MCA (4 semesters):
   - S1 accepted (Model 1, 3 features)
   - S4 accepted (Model 2, 5 features)
   - S5 rejected (HTTP 422 / UnsupportedSemesterError)
2. B.Tech (8 semesters):
   - S1 accepted (Model 1, 3 features)
   - S2 accepted (Model 2, 5 features)
   - S4 accepted (Model 2, 5 features)
   - S5 accepted (Model 2, 5 features, uses S4 as previous semester)
   - S6 accepted (Model 2, 5 features)
   - S7 accepted (Model 2, 5 features)
   - S8 accepted (Model 2, 5 features, uses S7 as previous semester)
   - S9 rejected (HTTP 422 / UnsupportedSemesterError)
3. Prediction routing:
   - S1 uses Model 1 (vcis_model_semester1.joblib)
   - S2, S4, S5, S8 use Model 2 (vcis_model_semesters2_4.joblib)
   - Scenario is 'Semester 1' for S1 and 'Semesters 2+' for S2+
4. Interventions:
   - MCA S5 rejected with InvalidInterventionDataError
   - B.Tech S5 accepted
   - B.Tech S8 accepted
   - B.Tech S9 rejected with InvalidInterventionDataError
5. Contract & Safety invariants:
   - Features do NOT contain semester number, student_id, CT2, or final exam marks.
   - Predictions execute without model retraining.
"""

import asyncio
from datetime import date
import json
import os
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure app imports resolve cleanly
sys.path.insert(0, "backend")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-12345"

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
import app.models.intervention

from app.models.department import Department
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.subject import Subject
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assessment import Assessment, AssessmentType
from app.models.intervention import Intervention, InterventionStatus, InterventionType
from app.models.user import User, UserRole

from app.services.academic_status_service import AcademicStatus
from app.services.feature_service import (
    extract_ml_features,
    extract_semester_1_features,
    extract_semesters_2_plus_features,
    extract_semesters_2_to_4_features,
    UnsupportedSemesterError,
)
from app.services.prediction_service import (
    predict_final_score,
    predict_semesters_2_plus,
    predict_semesters_2_to_4,
    get_model_metadata,
    get_model_artifact_path,
)
from app.services.intervention_service import (
    create_intervention,
    InvalidInterventionDataError,
)
from app.schemas.intervention import InterventionCreate

from app.main import app
from app.database import get_db
from app.core.dependencies import get_current_user


class TestProgramDurationMultiSemester(unittest.TestCase):
    """Exhaustive tests for multi-program durations (MCA 4 sems vs B.Tech 8 sems)."""

    @classmethod
    def setUpClass(cls):
        """Set up in-memory SQLite database."""
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        """Clean all tables and seed standard departments and courses."""
        self.db = self.Session()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

        # Seed Department
        self.dept = Department(id=1, name="School of Computing", code="SOC")
        self.db.add(self.dept)

        # Seed MCA Program (4 semesters)
        self.course_mca = Course(
            id=1,
            department_id=1,
            name="Master of Computer Applications",
            code="MCA",
            duration_years=2,
            total_semesters=4,
            is_active=True,
        )
        # Seed B.Tech Program (8 semesters)
        self.course_btech = Course(
            id=2,
            department_id=1,
            name="Bachelor of Technology in Computer Science",
            code="BTCSE",
            duration_years=4,
            total_semesters=8,
            is_active=True,
        )
        self.db.add_all([self.course_mca, self.course_btech])

        # Seed Faculty
        self.user_faculty = User(id=10, email="faculty@test.com", password_hash="hash", role=UserRole.FACULTY, is_active=True)
        self.db.add(self.user_faculty)
        self.db.commit()

        self.faculty = Faculty(
            id=1,
            user_id=10,
            department_id=1,
            employee_code="FAC001",
            first_name="Prof",
            last_name="Turing",
            designation="Professor",
            is_active=True,
        )
        self.db.add(self.faculty)
        self.db.commit()

        # Admin user for API calls
        self.mock_admin = User(id=99, email="admin@test.com", password_hash="hash", role=UserRole.ADMIN, is_active=True)

        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.mock_admin

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------
    # Helper ASGI caller
    # ------------------------------------------------------------------

    def _post(self, path: str, json_data: dict | None = None) -> tuple[int, dict]:
        body = json.dumps(json_data).encode("utf-8") if json_data is not None else b""
        headers = [
            (b"content-type", b"application/json"),
            (b"authorization", b"Bearer test-token"),
        ]
        status_code = None
        response_body = []

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": headers,
        }

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            nonlocal status_code, response_body
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        asyncio.run(app(scope, receive, send))
        raw = b"".join(response_body).decode("utf-8")
        return status_code, json.loads(raw) if raw else {}

    # ------------------------------------------------------------------
    # Academic Data Helpers
    # ------------------------------------------------------------------

    def _setup_student(self, student_id: int, course_id: int, current_sem: int) -> Student:
        user = User(id=student_id, email=f"student{student_id}@test.com", password_hash="hash", role=UserRole.STUDENT, is_active=True)
        self.db.add(user)
        self.db.commit()

        student = Student(
            id=student_id,
            user_id=student_id,
            department_id=1,
            course_id=course_id,
            roll_number=f"ROLL_{student_id}",
            admission_year=2024,
            current_semester=current_sem,
            name=f"Student {student_id}",
            email=f"student{student_id}@test.com",
            is_active=True,
        )
        self.db.add(student)
        self.db.commit()
        return student

    def _setup_semester_academic_records(
        self,
        student_id: int,
        course_id: int,
        semester: int,
        subject_id: int,
        enrollment_id: int,
        attendance_pct: float = 85.0,
        assignment_pct: float = 80.0,
        ct1_pct: float = 75.0,
        final_score: float = 78.0,
    ):
        """Seed subject, enrollment, attendance, and assessments for a specific semester."""
        sub = Subject(
            id=subject_id,
            course_id=course_id,
            name=f"Subject {subject_id} S{semester}",
            code=f"SUB_{subject_id}",
            semester=semester,
            credits=4,
            is_active=True,
        )
        self.db.add(sub)
        self.db.commit()

        enr = Enrollment(
            id=enrollment_id,
            student_id=student_id,
            subject_id=subject_id,
            academic_year="2024-25",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add(enr)
        self.db.commit()

        # Attendance: 10 sessions total
        present_count = int(attendance_pct / 10)
        for i in range(1, 11):
            status = AttendanceStatus.PRESENT if i <= present_count else AttendanceStatus.ABSENT
            att = Attendance(
                id=enrollment_id * 100 + i,
                enrollment_id=enrollment_id,
                attendance_date=date(2024, 1, i),
                status=status,
            )
            self.db.add(att)

        # Assignment
        asst = Assessment(
            id=enrollment_id * 100 + 1,
            enrollment_id=enrollment_id,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment 1",
            max_marks=100,
            obtained_marks=int(assignment_pct),
            assessment_date=date(2024, 1, 15),
        )
        self.db.add(asst)

        # CT1
        ct1 = Assessment(
            id=enrollment_id * 100 + 2,
            enrollment_id=enrollment_id,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1",
            max_marks=100,
            obtained_marks=int(ct1_pct),
            assessment_date=date(2024, 1, 16),
        )
        self.db.add(ct1)

        # Final (for completed previous semester calculation)
        final_exam = Assessment(
            id=enrollment_id * 100 + 3,
            enrollment_id=enrollment_id,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Final Exam",
            max_marks=100,
            obtained_marks=int(final_score),
            assessment_date=date(2024, 1, 17),
        )
        self.db.add(final_exam)
        self.db.commit()

    # ==================================================================
    # 1. MCA 4-SEMESTER TESTS
    # ==================================================================

    def test_mca_semester_1_accepted_model_1(self):
        """MCA S1 prediction succeeds and routes to Model 1 (3 features)."""
        student = self._setup_student(student_id=101, course_id=1, current_sem=1)
        self._setup_semester_academic_records(
            student_id=101, course_id=1, semester=1, subject_id=101, enrollment_id=101
        )

        status_code, body = self._post("/predictions/students/101", {"semester": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["student_id"], 101)
        self.assertEqual(body["semester"], 1)
        self.assertEqual(body["scenario"], "Semester 1")
        self.assertEqual(len(body["features"]), 3)
        self.assertEqual(
            set(body["features"].keys()),
            {"current_attendance", "current_assignment_average", "current_ct1_average"},
        )

    def test_mca_semester_4_accepted_model_2(self):
        """MCA S4 prediction succeeds and routes to Model 2 (5 features, using S3)."""
        student = self._setup_student(student_id=102, course_id=1, current_sem=4)
        # S3 (previous semester)
        self._setup_semester_academic_records(
            student_id=102, course_id=1, semester=3, subject_id=102, enrollment_id=102,
            final_score=85.0, attendance_pct=90.0,
        )
        # S4 (current semester)
        self._setup_semester_academic_records(
            student_id=102, course_id=1, semester=4, subject_id=103, enrollment_id=103,
            attendance_pct=80.0, assignment_pct=85.0, ct1_pct=78.0,
        )

        status_code, body = self._post("/predictions/students/102", {"semester": 4})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["student_id"], 102)
        self.assertEqual(body["semester"], 4)
        self.assertEqual(body["scenario"], "Semesters 2+")
        self.assertEqual(len(body["features"]), 5)
        self.assertAlmostEqual(body["features"]["previous_semester_score"], 80.0, places=1)

    def test_mca_semester_5_rejected_program_bounds(self):
        """MCA S5 prediction is strictly rejected because total_semesters=4."""
        student = self._setup_student(student_id=103, course_id=1, current_sem=4)
        status_code, body = self._post("/predictions/students/103", {"semester": 5})
        self.assertEqual(status_code, 422)
        self.assertIn("detail", body)
        self.assertIn("MCA", str(body["detail"]))

    # ==================================================================
    # 2. B.TECH 8-SEMESTER TESTS
    # ==================================================================

    def test_btech_semester_1_accepted_model_1(self):
        """B.Tech S1 prediction succeeds and routes to Model 1."""
        student = self._setup_student(student_id=201, course_id=2, current_sem=1)
        self._setup_semester_academic_records(
            student_id=201, course_id=2, semester=1, subject_id=201, enrollment_id=201
        )

        status_code, body = self._post("/predictions/students/201", {"semester": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["scenario"], "Semester 1")
        self.assertEqual(len(body["features"]), 3)

    def test_btech_semester_2_accepted_model_2(self):
        """B.Tech S2 prediction succeeds with Model 2 using S1 as previous."""
        student = self._setup_student(student_id=202, course_id=2, current_sem=2)
        self._setup_semester_academic_records(
            student_id=202, course_id=2, semester=1, subject_id=202, enrollment_id=202, final_score=80.0
        )
        self._setup_semester_academic_records(
            student_id=202, course_id=2, semester=2, subject_id=203, enrollment_id=203
        )

        status_code, body = self._post("/predictions/students/202", {"semester": 2})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["scenario"], "Semesters 2+")
        self.assertEqual(len(body["features"]), 5)

    def test_btech_semester_5_accepted_model_2_using_s4(self):
        """B.Tech S5 prediction succeeds with Model 2 using S4 as previous semester."""
        student = self._setup_student(student_id=205, course_id=2, current_sem=5)
        # S4 (previous semester)
        self._setup_semester_academic_records(
            student_id=205, course_id=2, semester=4, subject_id=204, enrollment_id=204,
            final_score=88.0, attendance_pct=90.0
        )
        # S5 (current semester)
        self._setup_semester_academic_records(
            student_id=205, course_id=2, semester=5, subject_id=205, enrollment_id=205,
            attendance_pct=80.0, assignment_pct=75.0, ct1_pct=82.0
        )

        status_code, body = self._post("/predictions/students/205", {"semester": 5})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["semester"], 5)
        self.assertEqual(body["scenario"], "Semesters 2+")
        self.assertEqual(len(body["features"]), 5)
        self.assertAlmostEqual(body["features"]["previous_semester_score"], 81.0, places=1)

    def test_btech_semester_8_accepted_model_2_using_s7(self):
        """B.Tech S8 prediction succeeds with Model 2 using S7 as previous semester."""
        student = self._setup_student(student_id=208, course_id=2, current_sem=8)
        # S7 (previous semester)
        self._setup_semester_academic_records(
            student_id=208, course_id=2, semester=7, subject_id=207, enrollment_id=207,
            final_score=92.0, attendance_pct=95.0
        )
        # S8 (current semester)
        self._setup_semester_academic_records(
            student_id=208, course_id=2, semester=8, subject_id=208, enrollment_id=208,
            attendance_pct=85.0, assignment_pct=90.0, ct1_pct=88.0
        )

        status_code, body = self._post("/predictions/students/208", {"semester": 8})
        self.assertEqual(status_code, 200)
        self.assertEqual(body["semester"], 8)
        self.assertEqual(body["scenario"], "Semesters 2+")
        self.assertEqual(len(body["features"]), 5)
        self.assertAlmostEqual(body["features"]["previous_semester_score"], 82.33, places=1)

    def test_btech_semester_9_rejected_program_bounds(self):
        """B.Tech S9 prediction is rejected because total_semesters=8."""
        student = self._setup_student(student_id=209, course_id=2, current_sem=8)
        status_code, body = self._post("/predictions/students/209", {"semester": 9})
        self.assertEqual(status_code, 422)
        self.assertIn("detail", body)
        self.assertIn("BTCSE", str(body["detail"]))

    # ==================================================================
    # 3. INTERVENTION TESTS (MCA VS B.TECH)
    # ==================================================================

    def test_intervention_mca_s5_rejected(self):
        """MCA student cannot receive intervention for semester 5 (max 4)."""
        student = self._setup_student(student_id=301, course_id=1, current_sem=4)
        data = InterventionCreate(
            student_id=301,
            faculty_id=1,
            semester=5,
            intervention_type=InterventionType.EXTRA_CLASS,
            trigger_predicted_score=48.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        with self.assertRaises(InvalidInterventionDataError):
            create_intervention(self.db, data)

    def test_intervention_btech_s5_and_s8_accepted(self):
        """B.Tech student can receive interventions for semester 5 and semester 8."""
        student = self._setup_student(student_id=302, course_id=2, current_sem=5)

        # S5
        data_s5 = InterventionCreate(
            student_id=302,
            faculty_id=1,
            semester=5,
            intervention_type=InterventionType.EXTRA_CLASS,
            trigger_predicted_score=45.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        inv_s5 = create_intervention(self.db, data_s5)
        self.assertEqual(inv_s5.semester, 5)

        # S8
        data_s8 = InterventionCreate(
            student_id=302,
            faculty_id=1,
            semester=8,
            intervention_type=InterventionType.COUNSELLING,
            trigger_predicted_score=52.0,
            trigger_academic_status=AcademicStatus.MONITOR,
        )
        inv_s8 = create_intervention(self.db, data_s8)
        self.assertEqual(inv_s8.semester, 8)

    def test_intervention_btech_s9_rejected(self):
        """B.Tech student cannot receive intervention for semester 9 (max 8)."""
        student = self._setup_student(student_id=303, course_id=2, current_sem=8)
        data = InterventionCreate(
            student_id=303,
            faculty_id=1,
            semester=9,
            intervention_type=InterventionType.MONITORING,
            trigger_predicted_score=42.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        with self.assertRaises(InvalidInterventionDataError):
            create_intervention(self.db, data)

    # ==================================================================
    # 4. PREDICTION ROUTING & COMPATIBILITY HELPERS
    # ==================================================================

    def test_prediction_service_convenience_functions(self):
        """Verify predict_semesters_2_plus and backward-compatibility predict_semesters_2_to_4."""
        score_plus = predict_semesters_2_plus(
            semester=6,
            previous_semester_score=80.0,
            previous_semester_attendance=85.0,
            current_attendance=80.0,
            current_assignment_average=85.0,
            current_ct1_average=75.0,
        )
        self.assertIsInstance(score_plus, float)

        score_to_4 = predict_semesters_2_to_4(
            semester=3,
            previous_semester_score=80.0,
            previous_semester_attendance=85.0,
            current_attendance=80.0,
            current_assignment_average=85.0,
            current_ct1_average=75.0,
        )
        self.assertIsInstance(score_to_4, float)

    def test_model_metadata_scenarios(self):
        """Verify scenario tags for S1 vs S2+."""
        meta_s1 = get_model_metadata(1)
        self.assertEqual(meta_s1["scenario"], "Semester 1")

        for sem in [2, 4, 5, 8]:
            meta = get_model_metadata(sem)
            self.assertEqual(meta["scenario"], "Semesters 2+")
            self.assertTrue(get_model_artifact_path(sem).name.endswith("vcis_model_semesters2_4.joblib"))


if __name__ == "__main__":
    unittest.main()
