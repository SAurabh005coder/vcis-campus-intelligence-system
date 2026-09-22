"""
VCIS 3.0 — Student Prediction IDOR & Authorization Security Tests

Validates:
1. Student A can execute prediction for Student A (HTTP 200).
2. Student A executing prediction for Student B is blocked (HTTP 403 Forbidden).
3. Student A attempting prediction for arbitrary/nonexistent student ID is blocked (HTTP 403 Forbidden, anti-enumeration).
4. Faculty can execute prediction for an authorized student (HTTP 200).
5. HOD can execute prediction for an authorized student (HTTP 200).
6. Admin can execute prediction for an authorized student (HTTP 200).
7. Invalid semester remains rejected according to existing schema validation (HTTP 422).
8. Student's own prediction response structure is fully preserved.
9. Academic status remains calculated from raw prediction before display rounding.
10. Feature keys match the fixed ML contract.
11. Invalid student ID (<= 0) returns HTTP 400 Bad Request.
12. Route alias /api/v1/predictions/students/{id} enforces identical IDOR protection.
"""

import asyncio
from datetime import date
import json
import os
import sys
import unittest

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-security-pred-secret-key-12345"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.base import Base
import app.models.user
import app.models.department
import app.models.course
import app.models.faculty
import app.models.student
import app.models.subject
import app.models.enrollment
import app.models.attendance
import app.models.assessment

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.models.assessment import Assessment, AssessmentType
from app.models.attendance import Attendance, AttendanceStatus
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User, UserRole
from app.services.academic_status_service import AcademicStatus, get_academic_status


class TestPredictionSecurity(unittest.TestCase):
    """Test suite verifying IDOR protection and role authorization on prediction endpoints."""

    @classmethod
    def setUpClass(cls):
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
        self.db = self.Session()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

        # Academic fixtures
        self.dept = Department(id=1, name="Computer Applications", code="MCA-DEPT")
        self.course = Course(
            id=1,
            department_id=1,
            name="Master of Computer Applications",
            code="MCA",
            duration_years=2,
            total_semesters=4,
        )
        self.subject_sem1 = Subject(
            id=101,
            course_id=1,
            name="Advanced Data Structures",
            code="MCA101",
            semester=1,
            credits=4,
        )
        self.db.add_all([self.dept, self.course, self.subject_sem1])

        # Users
        self.user_student_a = User(
            id=1,
            email="student_a@test.com",
            password_hash="pw_a",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_student_b = User(
            id=2,
            email="student_b@test.com",
            password_hash="pw_b",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_faculty = User(
            id=3,
            email="faculty@test.com",
            password_hash="pw_fac",
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_hod = User(
            id=4,
            email="hod@test.com",
            password_hash="pw_hod",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_admin = User(
            id=5,
            email="admin@test.com",
            password_hash="pw_adm",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.db.add_all([
            self.user_student_a,
            self.user_student_b,
            self.user_faculty,
            self.user_hod,
            self.user_admin,
        ])
        self.db.commit()

        # Seed Faculty profile for HOD
        self.faculty_hod = Faculty(
            id=1,
            user_id=4,
            department_id=1,
            employee_code="HOD-MCA-001",
            first_name="HOD",
            last_name="User",
            designation="Head of Department",
            is_active=True,
        )
        self.db.add(self.faculty_hod)

        # Student Profiles
        self.student_a = Student(
            id=10,
            user_id=1,
            department_id=1,
            course_id=1,
            roll_number="23MCA001",
            admission_year=2023,
            current_semester=1,
            name="Student A",
            email="student_a@test.com",
            is_active=True,
        )
        self.student_b = Student(
            id=20,
            user_id=2,
            department_id=1,
            course_id=1,
            roll_number="23MCA002",
            admission_year=2023,
            current_semester=1,
            name="Student B",
            email="student_b@test.com",
            is_active=True,
        )
        self.db.add_all([self.student_a, self.student_b])

        # Student A Academic Records
        self.enrollment_a = Enrollment(
            id=1,
            student_id=10,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.att_a1 = Attendance(
            id=1,
            enrollment_id=1,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
        )
        self.att_a2 = Attendance(
            id=2,
            enrollment_id=1,
            attendance_date=date(2023, 9, 2),
            status=AttendanceStatus.PRESENT,
        )
        self.ass_a1 = Assessment(
            id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst 1",
            max_marks=20,
            obtained_marks=18,
            assessment_date=date(2023, 9, 10),
        )
        self.ass_a2 = Assessment(
            id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT 1",
            max_marks=20,
            obtained_marks=16,
            assessment_date=date(2023, 9, 20),
        )

        # Student B Academic Records
        self.enrollment_b = Enrollment(
            id=2,
            student_id=20,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.att_b1 = Attendance(
            id=3,
            enrollment_id=2,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
        )
        self.ass_b1 = Assessment(
            id=3,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst 1",
            max_marks=20,
            obtained_marks=14,
            assessment_date=date(2023, 9, 10),
        )
        self.ass_b2 = Assessment(
            id=4,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT 1",
            max_marks=20,
            obtained_marks=12,
            assessment_date=date(2023, 9, 20),
        )

        self.db.add_all([
            self.enrollment_a,
            self.att_a1,
            self.att_a2,
            self.ass_a1,
            self.ass_a2,
            self.enrollment_b,
            self.att_b1,
            self.ass_b1,
            self.ass_b2,
        ])
        self.db.commit()

        self.active_user = None
        app.dependency_overrides[get_db] = lambda: self.db

        def override_current_user():
            if self.active_user is None:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            return self.active_user

        app.dependency_overrides[get_current_user] = override_current_user

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()

    def _post(
        self,
        path: str,
        json_data: dict | None = None,
        user: User | None = None,
    ) -> tuple[int, dict]:
        self.active_user = user
        body = json.dumps(json_data).encode("utf-8") if json_data is not None else b""
        headers = [(b"content-type", b"application/json")]
        if user is not None:
            headers.append((b"authorization", b"Bearer mock-token"))

        response_body = []
        status_code = [0]

        async def send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": headers,
        }

        body_sent = False

        async def receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(app(scope, receive, send))
        finally:
            loop.close()

        resp_text = b"".join(response_body).decode("utf-8")
        try:
            resp_json = json.loads(resp_text)
        except Exception:
            resp_json = {"raw": resp_text}
        return status_code[0], resp_json

    # ==================================================================
    # TEST CASES
    # ==================================================================

    def test_01_student_a_predicts_student_a(self):
        """TEST 1: Student A predicts Student A -> HTTP 200."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)
        self.assertEqual(data["semester"], 1)
        self.assertIn("predicted_final_semester_score", data)
        self.assertIn("academic_status", data)

    def test_02_student_a_predicts_student_b(self):
        """TEST 2: Student A predicts Student B -> HTTP 403 Forbidden."""
        status, data = self._post(
            f"/predictions/students/{self.student_b.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_03_student_a_attempts_prediction_for_nonexistent_student(self):
        """TEST 3: Student A attempts prediction for nonexistent student ID -> HTTP 403 Forbidden."""
        status, data = self._post(
            "/predictions/students/9999",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_04_faculty_can_predict_student(self):
        """TEST 4: Faculty can predict an authorized student -> HTTP 200."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)

    def test_05_hod_can_predict_student(self):
        """TEST 5: HOD can predict an authorized student -> HTTP 200."""
        status, data = self._post(
            f"/predictions/students/{self.student_b.id}",
            {"semester": 1},
            user=self.user_hod,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_b.id)

    def test_06_admin_can_predict_student(self):
        """TEST 6: Admin can predict an authorized student -> HTTP 200."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_admin,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)

    def test_07_invalid_semester_rejected(self):
        """TEST 7: Invalid semester remains rejected with HTTP 422 Unprocessable Entity."""
        invalid_semesters = [0, 5, -1]
        for sem in invalid_semesters:
            status, _ = self._post(
                f"/predictions/students/{self.student_a.id}",
                {"semester": sem},
                user=self.user_student_a,
            )
            self.assertEqual(status, 422)

    def test_08_student_own_prediction_response_structure(self):
        """TEST 8: Student's own prediction response remains unchanged in structure."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        expected_fields = {
            "student_id",
            "semester",
            "predicted_final_semester_score",
            "academic_status",
            "model_version",
            "model_type",
            "scenario",
            "features",
        }
        self.assertTrue(expected_fields.issubset(set(data.keys())))

    def test_09_academic_status_from_raw_prediction(self):
        """TEST 9: Academic status remains calculated from raw prediction before display rounding."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        score = data["predicted_final_semester_score"]
        act_status = data["academic_status"]
        expected_status = get_academic_status(score).value
        self.assertEqual(act_status, expected_status)

    def test_10_feature_keys_match_model_contract(self):
        """TEST 10: Feature keys remain exactly the model-defined keys for Semester 1."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        expected_feature_keys = {
            "current_attendance",
            "current_assignment_average",
            "current_ct1_average",
        }
        self.assertEqual(set(data["features"].keys()), expected_feature_keys)

    def test_11_invalid_student_id_returns_400(self):
        """TEST 11: Invalid student ID (<= 0) returns HTTP 400 Bad Request."""
        status_0, data_0 = self._post(
            "/predictions/students/0",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status_0, 400)
        self.assertIn("Invalid student ID", data_0.get("detail", ""))

        status_neg, data_neg = self._post(
            "/predictions/students/-1",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status_neg, 400)

    def test_12_route_alias_enforces_same_security(self):
        """TEST 12: Route alias /api/v1/predictions/students/{id} enforces identical IDOR protection."""
        # Own prediction succeeds
        status, data = self._post(
            f"/api/v1/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)

        # Cross-student prediction is blocked
        status_blocked, _ = self._post(
            f"/api/v1/predictions/students/{self.student_b.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status_blocked, 403)


if __name__ == "__main__":
    unittest.main()
