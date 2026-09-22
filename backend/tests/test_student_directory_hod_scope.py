"""
VCIS 3.0 — Student Directory HOD Department Scope Security Tests

Validates:
1. HOD with department 1 sees students from department 1.
2. HOD with department 1 does NOT see students from department 2.
3. HOD with department 2 sees students from department 2.
4. HOD cannot bypass scope using query parameters (e.g. ?department_id=2).
5. HOD with no Faculty profile receives 403.
6. HOD with Faculty profile but department_id=None receives 403.
7. HOD receives only their department even when students from multiple departments exist.
8. ADMIN retains access to students across departments.
9. FACULTY retains existing access behavior (all students returned).
10. STUDENT cannot access the general student directory -> 403.
11. Unauthenticated request retains existing 401 behavior.
12. Existing search/query parameters do not expand or bypass HOD scope.
13. No client-provided department_id can expand HOD scope.
14. /api/v1/students/me remains unaffected for students.
"""

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-student-directory-hod-scope-secret-key-12345"

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


class TestStudentDirectoryHodScope(unittest.TestCase):
    """Test suite verifying department-scoped student directory access for HOD users."""

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

        # 1. Departments & Courses
        self.dept_1 = Department(id=1, name="Computer Science and Engineering", code="CSE", is_active=True)
        self.dept_2 = Department(id=2, name="Electronics and Communication", code="ECE", is_active=True)
        self.course_1 = Course(id=1, department_id=1, name="B.Tech CSE", code="BTCSE", duration_years=4, total_semesters=8, is_active=True)
        self.course_2 = Course(id=2, department_id=2, name="B.Tech ECE", code="BTECE", duration_years=4, total_semesters=8, is_active=True)
        self.db.add_all([self.dept_1, self.dept_2, self.course_1, self.course_2])

        # 2. Users
        self.user_hod_dept1 = User(id=1, email="hod1@test.com", password_hash="hash", role=UserRole.HOD, is_active=True)
        self.user_hod_dept2 = User(id=2, email="hod2@test.com", password_hash="hash", role=UserRole.HOD, is_active=True)
        self.user_hod_orphan = User(id=3, email="hod_orphan@test.com", password_hash="hash", role=UserRole.HOD, is_active=True)
        self.user_faculty = User(id=4, email="faculty@test.com", password_hash="hash", role=UserRole.FACULTY, is_active=True)
        self.user_admin = User(id=5, email="admin@test.com", password_hash="hash", role=UserRole.ADMIN, is_active=True)
        self.user_student_1 = User(id=6, email="student1@test.com", password_hash="hash", role=UserRole.STUDENT, is_active=True)
        self.user_student_2 = User(id=7, email="student2@test.com", password_hash="hash", role=UserRole.STUDENT, is_active=True)
        self.db.add_all([
            self.user_hod_dept1,
            self.user_hod_dept2,
            self.user_hod_orphan,
            self.user_faculty,
            self.user_admin,
            self.user_student_1,
            self.user_student_2,
        ])
        self.db.commit()

        # 3. Faculty Profiles (HODs & Faculty)
        self.faculty_hod1 = Faculty(
            id=1,
            user_id=self.user_hod_dept1.id,
            department_id=self.dept_1.id,
            employee_code="HOD-CSE-001",
            first_name="HOD",
            last_name="One",
            designation="Head of Department CSE",
            is_active=True,
        )
        self.faculty_hod2 = Faculty(
            id=2,
            user_id=self.user_hod_dept2.id,
            department_id=self.dept_2.id,
            employee_code="HOD-ECE-001",
            first_name="HOD",
            last_name="Two",
            designation="Head of Department ECE",
            is_active=True,
        )
        self.faculty_general = Faculty(
            id=3,
            user_id=self.user_faculty.id,
            department_id=self.dept_1.id,
            employee_code="FAC-CSE-001",
            first_name="General",
            last_name="Faculty",
            designation="Professor",
            is_active=True,
        )
        self.db.add_all([self.faculty_hod1, self.faculty_hod2, self.faculty_general])

        # 4. Students across Departments
        # Students in Dept 1
        self.student_d1_a = Student(
            id=101,
            user_id=self.user_student_1.id,
            department_id=self.dept_1.id,
            course_id=self.course_1.id,
            roll_number="CSE001",
            admission_year=2023,
            current_semester=3,
            name="Alice CSE",
            email="student1@test.com",
            is_active=True,
        )
        self.student_d1_b = Student(
            id=102,
            user_id=998,
            department_id=self.dept_1.id,
            course_id=self.course_1.id,
            roll_number="CSE002",
            admission_year=2023,
            current_semester=3,
            name="Bob CSE",
            email="bob.cse@test.com",
            is_active=True,
        )
        # Students in Dept 2
        self.student_d2_a = Student(
            id=201,
            user_id=self.user_student_2.id,
            department_id=self.dept_2.id,
            course_id=self.course_2.id,
            roll_number="ECE001",
            admission_year=2023,
            current_semester=3,
            name="Charlie ECE",
            email="student2@test.com",
            is_active=True,
        )
        self.student_d2_b = Student(
            id=202,
            user_id=999,
            department_id=self.dept_2.id,
            course_id=self.course_2.id,
            roll_number="ECE002",
            admission_year=2023,
            current_semester=3,
            name="Diana ECE",
            email="diana.ece@test.com",
            is_active=True,
        )
        self.db.add_all([
            self.student_d1_a,
            self.student_d1_b,
            self.student_d2_a,
            self.student_d2_b,
        ])
        self.db.commit()

        self.active_user = None
        app.dependency_overrides[get_db] = lambda: self.db

        def override_current_user():
            if self.active_user is None:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Not authenticated")
            return self.active_user

        app.dependency_overrides[get_current_user] = override_current_user

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()

    def _get(self, path: str, user: User | None = None) -> tuple[int, list | dict]:
        headers = [(b"content-type", b"application/json")]
        if user is not None:
            self.active_user = user
            headers.append((b"authorization", b"Bearer mock-token"))
        else:
            self.active_user = None

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

    # =========================================================================
    # TEST CASES
    # =========================================================================

    def test_01_hod_dept1_sees_only_dept1_students(self):
        """1. HOD with department 1 sees students from department 1."""
        status, data = self._get("/api/v1/students/", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        dept_ids = {s["department_id"] for s in data}
        self.assertEqual(dept_ids, {self.dept_1.id})
        student_ids = {s["id"] for s in data}
        self.assertEqual(student_ids, {101, 102})

    def test_02_hod_dept1_does_not_see_dept2_students(self):
        """2. HOD with department 1 does NOT see students from department 2."""
        status, data = self._get("/api/v1/students/", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        student_ids = {s["id"] for s in data}
        self.assertNotIn(201, student_ids)
        self.assertNotIn(202, student_ids)

    def test_03_hod_dept2_sees_only_dept2_students(self):
        """3. HOD with department 2 sees students from department 2."""
        status, data = self._get("/api/v1/students/", user=self.user_hod_dept2)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        dept_ids = {s["department_id"] for s in data}
        self.assertEqual(dept_ids, {self.dept_2.id})
        student_ids = {s["id"] for s in data}
        self.assertEqual(student_ids, {201, 202})

    def test_04_hod_cannot_bypass_scope_using_query_parameters(self):
        """4. HOD cannot bypass scope using query parameters (e.g. ?department_id=2)."""
        # HOD 1 attempts to pass ?department_id=2 or other query params
        status, data = self._get("/api/v1/students/?department_id=2", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 2)
        dept_ids = {s["department_id"] for s in data}
        self.assertEqual(dept_ids, {self.dept_1.id})
        student_ids = {s["id"] for s in data}
        self.assertNotIn(201, student_ids)
        self.assertNotIn(202, student_ids)

    def test_05_hod_with_no_faculty_profile_receives_403(self):
        """5. HOD with no Faculty profile receives 403 Forbidden."""
        status, data = self._get("/api/v1/students/", user=self.user_hod_orphan)
        self.assertEqual(status, 403)
        self.assertIn("faculty profile", data.get("detail", "").lower())

    def test_06_hod_with_faculty_profile_null_department_receives_403(self):
        """6. HOD with Faculty profile but department_id=None receives 403 Forbidden."""
        # Create HOD user with unassigned department faculty record via mock query
        from unittest.mock import MagicMock
        mock_faculty = Faculty(
            id=99,
            user_id=self.user_hod_orphan.id,
            department_id=1,
            employee_code="HOD-NULL-001",
            first_name="Orphan",
            last_name="HOD",
            designation="Head of Department",
        )
        mock_faculty.department_id = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_faculty

        from app.core.authorization import resolve_hod_department_id
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_hod_orphan, mock_db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("assigned department", ctx.exception.detail.lower())

    def test_07_hod_receives_only_their_department_when_multiple_departments_exist(self):
        """7. HOD receives only their department even when students from multiple departments exist."""
        status1, data1 = self._get("/api/v1/students/", user=self.user_hod_dept1)
        self.assertEqual(status1, 200)
        for student in data1:
            self.assertEqual(student["department_id"], self.dept_1.id)

        status2, data2 = self._get("/api/v1/students/", user=self.user_hod_dept2)
        self.assertEqual(status2, 200)
        for student in data2:
            self.assertEqual(student["department_id"], self.dept_2.id)

    def test_08_admin_retains_access_to_students_across_departments(self):
        """8. ADMIN retains access to students across departments (all 4 students)."""
        status, data = self._get("/api/v1/students/", user=self.user_admin)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        dept_ids = {s["department_id"] for s in data}
        self.assertEqual(dept_ids, {self.dept_1.id, self.dept_2.id})

    def test_09_faculty_retains_existing_access_behavior(self):
        """9. FACULTY retains existing access behavior (all 4 students)."""
        status, data = self._get("/api/v1/students/", user=self.user_faculty)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        dept_ids = {s["department_id"] for s in data}
        self.assertEqual(dept_ids, {self.dept_1.id, self.dept_2.id})

    def test_10_student_cannot_access_general_student_directory(self):
        """10. STUDENT cannot access the general student directory -> 403 Forbidden."""
        status, data = self._get("/api/v1/students/", user=self.user_student_1)
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_11_unauthenticated_request_retains_401(self):
        """11. Unauthenticated request retains existing 401 behavior."""
        status, data = self._get("/api/v1/students/", user=None)
        self.assertEqual(status, 401)

    def test_12_existing_query_params_do_not_expand_or_bypass_hod_scope(self):
        """12. Existing search/filter parameters do not expand or bypass HOD scope."""
        status, data = self._get("/api/v1/students/?search=CSE&limit=100&offset=0", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        for s in data:
            self.assertEqual(s["department_id"], self.dept_1.id)

    def test_13_no_client_provided_department_id_can_expand_hod_scope(self):
        """13. No client-provided department_id can expand HOD scope."""
        status, data = self._get("/api/v1/students/?department_id=999&department_id=2", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        # Still strictly dept_1
        self.assertEqual(len(data), 2)
        for s in data:
            self.assertEqual(s["department_id"], self.dept_1.id)

    def test_14_students_me_remains_unaffected_for_students(self):
        """14. /api/v1/students/me remains unaffected for students."""
        status, data = self._get("/api/v1/students/me", user=self.user_student_1)
        self.assertEqual(status, 200)
        self.assertEqual(data["id"], self.student_d1_a.id)
        self.assertEqual(data["user_id"], self.user_student_1.id)
        self.assertEqual(data["name"], "Alice CSE")


if __name__ == "__main__":
    unittest.main()
