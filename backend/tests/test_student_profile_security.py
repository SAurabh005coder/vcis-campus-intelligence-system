"""
VCIS 3.0 — Student Profile IDOR & Authorization Security Tests

Validates:
1. Student A can retrieve own student profile (HTTP 200).
2. Student A retrieving Student B profile is blocked (HTTP 403 Forbidden).
3. Student A attempting to retrieve nonexistent student profile is blocked (HTTP 403 Forbidden, anti-enumeration).
4. Faculty can retrieve any student profile (HTTP 200).
5. HOD can retrieve any student profile (HTTP 200).
6. Admin can retrieve any student profile (HTTP 200).
7. Invalid/non-positive student ID preserves intended existing response:
   - For student: HTTP 403 Forbidden (preventing information disclosure).
   - For staff: HTTP 404 Not Found.
8. Response structure for authorized student matches StudentResponse schema.
"""

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-security-student-profile-key-12345"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.base import Base
import app.models.user
import app.models.department
import app.models.course
import app.models.student

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.models.course import Course
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.user import User, UserRole


class TestStudentProfileSecurity(unittest.TestCase):
    """Test suite verifying IDOR protection on GET /api/v1/students/{student_id}."""

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

        # Department & Course
        self.dept = Department(id=1, name="Computer Applications", code="MCA-DEPT")
        self.course = Course(
            id=1,
            department_id=1,
            name="Master of Computer Applications",
            code="MCA",
            duration_years=2,
            total_semesters=4,
        )
        self.db.add_all([self.dept, self.course])

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
        self.faculty_hod = Faculty(
            id=1,
            user_id=4,
            department_id=1,
            employee_code="HOD-MCA-001",
            first_name="HOD",
            last_name="MCA",
            designation="Head of Department",
            is_active=True,
        )
        self.db.add_all([
            self.user_student_a,
            self.user_student_b,
            self.user_faculty,
            self.user_hod,
            self.user_admin,
            self.faculty_hod,
        ])

        # Student Profiles
        self.student_a = Student(
            id=10,
            user_id=1,
            department_id=1,
            course_id=1,
            roll_number="23MCA001",
            admission_year=2023,
            current_semester=1,
            name="Alice Alpha",
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
            name="Bob Beta",
            email="student_b@test.com",
            is_active=True,
        )
        self.db.add_all([self.student_a, self.student_b])
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

    def _get(
        self,
        path: str,
        user: User | None = None,
    ) -> tuple[int, dict]:
        self.active_user = user
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
            "method": "GET",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": headers,
        }

        async def receive():
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

    def test_01_student_a_requests_own_profile(self):
        """TEST 1: Student A requests Student A profile -> HTTP 200."""
        status, data = self._get(
            f"/api/v1/students/{self.student_a.id}",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["id"], self.student_a.id)
        self.assertEqual(data["user_id"], self.user_student_a.id)
        self.assertEqual(data["roll_number"], "23MCA001")
        self.assertEqual(data["name"], "Alice Alpha")

    def test_02_student_a_requests_student_b_profile(self):
        """TEST 2: Student A requests Student B profile -> HTTP 403 Forbidden."""
        status, data = self._get(
            f"/api/v1/students/{self.student_b.id}",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_03_student_a_requests_nonexistent_profile(self):
        """TEST 3: Student A requests nonexistent student ID -> HTTP 403 Forbidden (anti-enumeration)."""
        status, data = self._get(
            "/api/v1/students/9999",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_04_faculty_can_retrieve_student_profile(self):
        """TEST 4: Faculty can still retrieve a student profile -> HTTP 200."""
        status, data = self._get(
            f"/api/v1/students/{self.student_a.id}",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["id"], self.student_a.id)

        # Faculty can also retrieve student B
        status_b, data_b = self._get(
            f"/api/v1/students/{self.student_b.id}",
            user=self.user_faculty,
        )
        self.assertEqual(status_b, 200)
        self.assertEqual(data_b["id"], self.student_b.id)

    def test_05_hod_can_retrieve_student_profile(self):
        """TEST 5: HOD can still retrieve a student profile -> HTTP 200."""
        status, data = self._get(
            f"/api/v1/students/{self.student_b.id}",
            user=self.user_hod,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["id"], self.student_b.id)

    def test_06_admin_can_retrieve_student_profile(self):
        """TEST 6: Admin can still retrieve a student profile -> HTTP 200."""
        status, data = self._get(
            f"/api/v1/students/{self.student_a.id}",
            user=self.user_admin,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["id"], self.student_a.id)

    def test_07_invalid_or_nonpositive_student_id(self):
        """TEST 7: Invalid/non-positive student ID preserves intended existing response."""
        # For staff, querying nonexistent/non-positive returns HTTP 404
        status_staff_0, data_staff_0 = self._get(
            "/api/v1/students/0",
            user=self.user_admin,
        )
        self.assertEqual(status_staff_0, 404)
        self.assertIn("Student not found", data_staff_0["detail"])

        status_staff_neg, data_staff_neg = self._get(
            "/api/v1/students/-1",
            user=self.user_faculty,
        )
        self.assertEqual(status_staff_neg, 404)

        # For student caller, non-matching/non-positive returns HTTP 403 (anti-enumeration)
        status_stud_0, _ = self._get(
            "/api/v1/students/0",
            user=self.user_student_a,
        )
        self.assertEqual(status_stud_0, 403)

        status_stud_neg, _ = self._get(
            "/api/v1/students/-1",
            user=self.user_student_a,
        )
        self.assertEqual(status_stud_neg, 403)

    def test_08_response_structure_for_authorized_student(self):
        """TEST 8: Response structure for an authorized student remains unchanged."""
        status, data = self._get(
            f"/api/v1/students/{self.student_a.id}",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        expected_keys = {
            "id",
            "user_id",
            "department_id",
            "course_id",
            "roll_number",
            "admission_year",
            "current_semester",
            "name",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        }
        self.assertEqual(set(data.keys()), expected_keys)


if __name__ == "__main__":
    unittest.main()
