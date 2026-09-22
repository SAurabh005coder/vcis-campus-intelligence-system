"""
VCIS 3.0 — Student Results IDOR & Authorization Security Tests

Verifies that:
1. Student A can access own result summary (HTTP 200).
2. Student A accessing Student B's result summary is blocked (HTTP 403 Forbidden).
3. Student A can access own semester result (HTTP 200).
4. Student A accessing Student B's semester result is blocked (HTTP 403 Forbidden).
5. Student A can access own enrollment result (HTTP 200).
6. Student A accessing Student B's enrollment result is blocked (HTTP 403 Forbidden).
7. Student A accessing Student B's enrollment performance is blocked (HTTP 403 Forbidden).
8. Student A can access own enrollment performance (HTTP 200).
9. Faculty access to results remains authorized (HTTP 200).
10. HOD access to results remains authorized (HTTP 200).
11. Admin access to results remains authorized (HTTP 200).
12. Nonexistent student ID behavior remains consistent (HTTP 404 for authorized roles / HTTP 403 for student).
13. Nonexistent enrollment ID returns HTTP 404 Not Found.
14. Invalid semester (<= 0) returns HTTP 400 Bad Request.
15. Invalid student ID (<= 0) and enrollment ID (<= 0) return HTTP 400 Bad Request.
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
os.environ["JWT_SECRET_KEY"] = "test-security-results-key-12345"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.base import Base
import app.models.user
import app.models.department
import app.models.course
import app.models.subject
import app.models.student
import app.models.enrollment
import app.models.attendance
import app.models.assessment

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.models.assessment import Assessment, AssessmentType
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User, UserRole


class TestResultsSecurity(unittest.TestCase):
    """Test suite verifying results authorization and IDOR protection."""

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

        # Seed Department, Course, Subject
        self.dept = Department(id=1, name="Computer Science", code="CS")
        self.course = Course(
            id=1,
            department_id=1,
            name="MCA",
            code="MCA",
            duration_years=2,
            total_semesters=4,
        )
        self.subject_sem1 = Subject(
            id=10,
            course_id=1,
            name="Data Structures",
            code="CS101",
            semester=1,
            credits=4,
        )
        self.db.add_all([self.dept, self.course, self.subject_sem1])

        # Seed Users
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

        # Seed Student Profiles
        self.student_a = Student(
            id=101,
            user_id=1,
            department_id=1,
            course_id=1,
            roll_number="23MCA001",
            admission_year=2023,
            current_semester=1,
            name="Student Alpha",
            email="student_a@test.com",
            is_active=True,
        )
        self.student_b = Student(
            id=102,
            user_id=2,
            department_id=1,
            course_id=1,
            roll_number="23MCA002",
            admission_year=2023,
            current_semester=1,
            name="Student Beta",
            email="student_b@test.com",
            is_active=True,
        )
        self.db.add_all([self.student_a, self.student_b])

        # Seed Enrollments
        self.enrollment_a = Enrollment(
            id=501,
            student_id=101,
            subject_id=10,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment_b = Enrollment(
            id=502,
            student_id=102,
            subject_id=10,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add_all([self.enrollment_a, self.enrollment_b])

        # Seed Assessments
        self.assessment_a = Assessment(
            id=701,
            enrollment_id=501,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1",
            max_marks=50.0,
            obtained_marks=42.0,
            assessment_date=date(2023, 9, 20),
        )
        self.assessment_b = Assessment(
            id=702,
            enrollment_id=502,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1",
            max_marks=50.0,
            obtained_marks=35.0,
            assessment_date=date(2023, 9, 20),
        )
        self.db.add_all([self.assessment_a, self.assessment_b])
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

    def _request(
        self,
        method: str,
        path: str,
        user: User | None = None,
        json_data: dict | None = None,
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
            "method": method.upper(),
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

    def test_01_student_a_accesses_own_result_summary(self):
        """TEST 1: Student A accesses own result summary -> HTTP 200."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)
        self.assertEqual(len(data["subjects"]), 1)
        self.assertEqual(data["total_subjects"], 1)

    def test_02_student_a_accesses_student_b_result_summary(self):
        """TEST 2: Student A accesses Student B result summary -> HTTP 403 Forbidden."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_b.id}/summary",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_03_student_a_accesses_own_semester_result(self):
        """TEST 3: Student A accesses own semester result -> HTTP 200."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)
        self.assertEqual(data["semester"], 1)

    def test_04_student_a_accesses_student_b_semester_result(self):
        """TEST 4: Student A accesses Student B semester result -> HTTP 403 Forbidden."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_b.id}/semester/1",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_05_student_a_accesses_own_enrollment_result(self):
        """TEST 5: Student A accesses own enrollment result -> HTTP 200."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["enrollment_id"], self.enrollment_a.id)
        self.assertEqual(data["student_id"], self.student_a.id)

    def test_06_student_a_accesses_student_b_enrollment_result(self):
        """TEST 6: Student A accesses Student B enrollment result -> HTTP 403 Forbidden."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_07_student_a_accesses_student_b_enrollment_performance(self):
        """TEST 7: Student A accesses Student B enrollment performance -> HTTP 403 Forbidden."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}/performance",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_08_student_a_accesses_own_enrollment_performance(self):
        """Verify Student A can access own enrollment performance -> HTTP 200."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["enrollment_id"], self.enrollment_a.id)
        self.assertEqual(data["student_id"], self.student_a.id)

    def test_09_faculty_access_remains_authorized(self):
        """TEST 8: Faculty access to authorized result remains HTTP 200."""
        # Summary
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)
        # Enrollment
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)
        # Performance
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)

    def test_10_hod_access_remains_authorized(self):
        """TEST 9: HOD access remains HTTP 200."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_b.id}/summary",
            user=self.user_hod,
        )
        self.assertEqual(status, 200)

        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}",
            user=self.user_hod,
        )
        self.assertEqual(status, 200)

    def test_11_admin_access_remains_authorized(self):
        """TEST 10: Admin access remains HTTP 200."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            user=self.user_admin,
        )
        self.assertEqual(status, 200)

        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}/performance",
            user=self.user_admin,
        )
        self.assertEqual(status, 200)

    def test_12_nonexistent_student_id_behavior(self):
        """Verify nonexistent student ID behavior remains consistent."""
        # For authorized staff, nonexistent student returns HTTP 404 (no enrollments)
        status, _ = self._request(
            "GET",
            "/api/v1/results/student/9999/summary",
            user=self.user_faculty,
        )
        self.assertEqual(status, 404)

        # For student caller, querying a student ID they do not own returns HTTP 403 (anti-enumeration)
        status, _ = self._request(
            "GET",
            "/api/v1/results/student/9999/summary",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)

    def test_13_nonexistent_enrollment_id_returns_404(self):
        """Verify nonexistent enrollment ID returns HTTP 404."""
        status, _ = self._request(
            "GET",
            "/api/v1/results/enrollment/99999",
            user=self.user_student_a,
        )
        self.assertEqual(status, 404)

        status, _ = self._request(
            "GET",
            "/api/v1/results/enrollment/99999/performance",
            user=self.user_admin,
        )
        self.assertEqual(status, 404)

    def test_14_invalid_parameters_return_400(self):
        """Verify invalid parameters (<= 0) return HTTP 400 Bad Request."""
        # Invalid student_id
        status, _ = self._request(
            "GET",
            "/api/v1/results/student/0/summary",
            user=self.user_student_a,
        )
        self.assertEqual(status, 400)

        # Invalid semester
        status, _ = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/semester/0",
            user=self.user_student_a,
        )
        self.assertEqual(status, 400)

        # Invalid enrollment_id
        status, _ = self._request(
            "GET",
            "/api/v1/results/enrollment/0",
            user=self.user_student_a,
        )
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
