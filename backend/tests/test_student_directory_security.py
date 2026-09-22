"""
VCIS 3.0 — Student Directory Exposure & /api/v1/students/me Security Tests

Validates:
1. STUDENT can GET /api/v1/students/me -> 200 OK.
2. /students/me returns the authenticated student's own Student record.
3. STUDENT GET /api/v1/students/ is blocked with HTTP 403 Forbidden.
4. STUDENT cannot bypass directory restriction using query parameters (e.g. ?limit=10).
5. FACULTY GET /api/v1/students/ -> 200 OK (all students returned).
6. HOD GET /api/v1/students/ -> 200 OK (all students returned).
7. ADMIN GET /api/v1/students/ -> 200 OK (all students returned).
8. STUDENT own /students/{own_id} remains HTTP 200 OK.
9. STUDENT another student's /students/{other_id} remains HTTP 403 Forbidden.
10. STUDENT nonexistent /students/{nonexistent_id} remains HTTP 403 Forbidden.
11. /students/me ignores arbitrary query parameters and does not accept/use student_id.
12. Response structure of /students/me matches StudentResponse schema.
13. STUDENT with no associated student record calling /students/me returns HTTP 404 Not Found.
"""

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-security-student-directory-key-12345"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.base import Base
import app.models.user
import app.models.department
import app.models.course
import app.models.faculty
import app.models.student

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.models.course import Course
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.user import User, UserRole


class TestStudentDirectorySecurity(unittest.TestCase):
    """Test suite verifying /students/me and generic student directory authorization."""

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
        self.user_student_orphan = User(
            id=3,
            email="student_orphan@test.com",
            password_hash="pw_orphan",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_faculty = User(
            id=4,
            email="faculty@test.com",
            password_hash="pw_fac",
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_hod = User(
            id=5,
            email="hod@test.com",
            password_hash="pw_hod",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_admin = User(
            id=6,
            email="admin@test.com",
            password_hash="pw_adm",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.db.add_all([
            self.user_student_a,
            self.user_student_b,
            self.user_student_orphan,
            self.user_faculty,
            self.user_hod,
            self.user_admin,
        ])
        self.db.commit()

        # Seed Faculty record for HOD
        self.faculty_hod = Faculty(
            id=1,
            user_id=self.user_hod.id,
            department_id=self.dept.id,
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

        raw_path = path.split("?")[0].encode("ascii")
        query_string = path.split("?")[1].encode("ascii") if "?" in path else b""

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "path": path.split("?")[0],
            "raw_path": raw_path,
            "query_string": query_string,
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

    def test_01_student_can_get_students_me(self):
        """TEST 1: STUDENT can GET /api/v1/students/me -> HTTP 200."""
        status, data = self._get(
            "/api/v1/students/me",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)

    def test_02_students_me_returns_authenticated_student_record(self):
        """TEST 2: /students/me returns authenticated student's own record."""
        # Student A
        status_a, data_a = self._get(
            "/api/v1/students/me",
            user=self.user_student_a,
        )
        self.assertEqual(status_a, 200)
        self.assertEqual(data_a["id"], self.student_a.id)
        self.assertEqual(data_a["user_id"], self.user_student_a.id)
        self.assertEqual(data_a["name"], "Alice Alpha")
        self.assertEqual(data_a["roll_number"], "23MCA001")

        # Student B
        status_b, data_b = self._get(
            "/api/v1/students/me",
            user=self.user_student_b,
        )
        self.assertEqual(status_b, 200)
        self.assertEqual(data_b["id"], self.student_b.id)
        self.assertEqual(data_b["user_id"], self.user_student_b.id)
        self.assertEqual(data_b["name"], "Bob Beta")
        self.assertEqual(data_b["roll_number"], "23MCA002")

    def test_03_student_get_students_directory_is_blocked(self):
        """TEST 3: STUDENT GET /api/v1/students/ -> HTTP 403 Forbidden."""
        status, data = self._get(
            "/api/v1/students/",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_04_student_cannot_bypass_directory_restriction_with_query_params(self):
        """TEST 4: STUDENT cannot use query parameters to bypass directory restriction."""
        status, data = self._get(
            "/api/v1/students/?limit=10&offset=0&department_id=1",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)

    def test_05_faculty_get_students_directory_succeeds(self):
        """TEST 5: FACULTY GET /api/v1/students/ -> HTTP 200 OK (all students)."""
        status, data = self._get(
            "/api/v1/students/",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_06_hod_get_students_directory_succeeds(self):
        """TEST 6: HOD GET /api/v1/students/ -> HTTP 200 OK."""
        status, data = self._get(
            "/api/v1/students/",
            user=self.user_hod,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_07_admin_get_students_directory_succeeds(self):
        """TEST 7: ADMIN GET /api/v1/students/ -> HTTP 200 OK."""
        status, data = self._get(
            "/api/v1/students/",
            user=self.user_admin,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_08_student_own_profile_by_id_remains_200(self):
        """TEST 8: STUDENT own /students/{id} remains HTTP 200."""
        status, data = self._get(
            f"/api/v1/students/{self.student_a.id}",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["id"], self.student_a.id)

    def test_09_student_other_profile_by_id_remains_403(self):
        """TEST 9: STUDENT another student's /students/{id} remains HTTP 403."""
        status, data = self._get(
            f"/api/v1/students/{self.student_b.id}",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)

    def test_10_student_nonexistent_profile_by_id_remains_403(self):
        """TEST 10: STUDENT nonexistent /students/{id} remains HTTP 403."""
        status, data = self._get(
            "/api/v1/students/9999",
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)

    def test_11_students_me_ignores_query_params_and_uses_token_identity(self):
        """TEST 11: /students/me ignores arbitrary query parameters and does not use student_id param."""
        status, data = self._get(
            f"/api/v1/students/me?student_id={self.student_b.id}&role=admin",
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        # MUST return Student A (Alice Alpha), NEVER Student B
        self.assertEqual(data["id"], self.student_a.id)
        self.assertEqual(data["name"], "Alice Alpha")

    def test_12_students_me_response_structure_matches_schema(self):
        """TEST 12: Response structure of /students/me matches StudentResponse."""
        status, data = self._get(
            "/api/v1/students/me",
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

    def test_13_orphan_student_user_returns_404(self):
        """TEST 13: Student user without student profile record returns HTTP 404."""
        status, data = self._get(
            "/api/v1/students/me",
            user=self.user_student_orphan,
        )
        self.assertEqual(status, 404)
        self.assertIn("Student profile not found", data.get("detail", ""))


if __name__ == "__main__":
    unittest.main()
