"""
VCIS 3.0 — Enrollment Roster Exposure & Detail IDOR Security Tests

Validates:
DIRECTORY:
1. STUDENT GET /api/v1/enrollments/ -> HTTP 403 Forbidden.
2. STUDENT GET /api/v1/enrollments/?student_id=<other> -> HTTP 403 Forbidden.
3. STUDENT GET /api/v1/enrollments/?academic_year=2023-24&status=enrolled -> HTTP 403 Forbidden.
4. FACULTY GET /api/v1/enrollments/ -> HTTP 200 OK.
5. HOD GET /api/v1/enrollments/ -> HTTP 200 OK.
6. ADMIN GET /api/v1/enrollments/ -> HTTP 200 OK.

DETAIL:
7. STUDENT accesses own enrollment -> HTTP 200 OK with verified schema.
8. STUDENT accesses another student's enrollment -> HTTP 403 Forbidden.
9. STUDENT accesses nonexistent enrollment ID -> HTTP 403 Forbidden (anti-enumeration).
10. FACULTY accesses enrollment detail -> HTTP 200 OK.
11. HOD accesses enrollment detail -> HTTP 200 OK.
12. ADMIN accesses enrollment detail -> HTTP 200 OK.
13. STAFF accesses nonexistent enrollment -> HTTP 404 Not Found.

REGRESSION PRESERVATION:
14. Student attendance roster -> 403 Forbidden.
15. Student assessment roster -> 403 Forbidden.
16. Student attendance detail (own) -> 200 OK.
17. Student assessment detail (own) -> 200 OK.
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
os.environ["JWT_SECRET_KEY"] = "test-security-enrollment-secret-key-12345"

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


class TestEnrollmentSecurity(unittest.TestCase):
    """Regression test suite verifying authorization rules on Enrollment list and detail endpoints."""

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

        # Department, Course, Subject
        self.dept = Department(id=1, name="Computer Applications", code="MCA-DEPT")
        self.course = Course(
            id=1,
            department_id=1,
            name="Master of Computer Applications",
            code="MCA",
            duration_years=2,
            total_semesters=4,
        )
        self.subject = Subject(
            id=101,
            course_id=1,
            name="Data Structures",
            code="MCA101",
            semester=1,
            credits=4,
        )
        self.db.add_all([self.dept, self.course, self.subject])

        # Users: Student A, Student B, Faculty, HOD, Admin
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

        # Student A & Enrollment A
        self.student_a = Student(
            id=10,
            user_id=1,
            department_id=1,
            course_id=1,
            roll_number="23MCA001",
            admission_year=2023,
            current_semester=1,
            name="Alice Student",
            email="student_a@test.com",
            is_active=True,
        )
        self.enrollment_a = Enrollment(
            id=1,
            student_id=10,
            subject_id=101,
            academic_year="2023-24",
            status=EnrollmentStatus.ENROLLED,
        )

        # Student B & Enrollment B
        self.student_b = Student(
            id=20,
            user_id=2,
            department_id=1,
            course_id=1,
            roll_number="23MCA002",
            admission_year=2023,
            current_semester=1,
            name="Bob Student",
            email="student_b@test.com",
            is_active=True,
        )
        self.enrollment_b = Enrollment(
            id=2,
            student_id=20,
            subject_id=101,
            academic_year="2023-24",
            status=EnrollmentStatus.ENROLLED,
        )

        self.db.add_all([
            self.student_a,
            self.enrollment_a,
            self.student_b,
            self.enrollment_b,
        ])

        # Attendance & Assessment fixtures for regression testing
        self.att_a = Attendance(
            id=101,
            enrollment_id=1,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
            remarks="Alice present",
        )
        self.ass_a = Assessment(
            id=201,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1",
            max_marks=50,
            obtained_marks=44,
            assessment_date=date(2023, 9, 20),
            remarks="Alice score",
        )
        self.db.add_all([self.att_a, self.ass_a])
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

        async def run_app():
            await app(scope, None, send)

        asyncio.run(run_app())

        body_bytes = b"".join(response_body)
        try:
            data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            data = {"raw": body_bytes.decode("utf-8", errors="replace")}

        return status_code[0], data

    # -------------------------------------------------------------------------
    # DIRECTORY TESTS
    # -------------------------------------------------------------------------

    def test_01_student_get_enrollments_directory_forbidden(self):
        """1. STUDENT GET /api/v1/enrollments/ -> 403 Forbidden."""
        code, data = self._get("/api/v1/enrollments/", user=self.user_student_a)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_02_student_get_enrollments_with_student_id_param_forbidden(self):
        """2. STUDENT GET /api/v1/enrollments/?student_id=<other> -> 403 Forbidden."""
        code, data = self._get("/api/v1/enrollments/?student_id=20", user=self.user_student_a)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_03_student_get_enrollments_with_other_filters_forbidden(self):
        """3. STUDENT GET /api/v1/enrollments/ with other filters -> 403 Forbidden."""
        code, data = self._get("/api/v1/enrollments/?academic_year=2023-24&status=enrolled", user=self.user_student_a)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_04_faculty_get_enrollments_directory_success(self):
        """4. FACULTY GET /api/v1/enrollments/ -> 200 OK with records."""
        code, data = self._get("/api/v1/enrollments/", user=self.user_faculty)
        self.assertEqual(code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_05_hod_get_enrollments_directory_success(self):
        """5. HOD GET /api/v1/enrollments/ -> 200 OK with records."""
        code, data = self._get("/api/v1/enrollments/", user=self.user_hod)
        self.assertEqual(code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    def test_06_admin_get_enrollments_directory_success(self):
        """6. ADMIN GET /api/v1/enrollments/ -> 200 OK with records."""
        code, data = self._get("/api/v1/enrollments/", user=self.user_admin)
        self.assertEqual(code, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)

    # -------------------------------------------------------------------------
    # DETAIL TESTS
    # -------------------------------------------------------------------------

    def test_07_student_accesses_own_enrollment_success(self):
        """7. STUDENT accesses own enrollment -> 200 OK with verified schema."""
        code, data = self._get("/api/v1/enrollments/1", user=self.user_student_a)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["student_id"], 10)
        self.assertEqual(data["subject_id"], 101)
        self.assertEqual(data["academic_year"], "2023-24")
        self.assertEqual(data["status"], "enrolled")
        self.assertIn("enrollment_date", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_08_student_accesses_other_student_enrollment_forbidden(self):
        """8. STUDENT accesses another student's enrollment -> 403 Forbidden."""
        code, data = self._get("/api/v1/enrollments/2", user=self.user_student_a)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_09_student_accesses_nonexistent_enrollment_anti_enumeration(self):
        """9. STUDENT accesses nonexistent enrollment ID -> 403 Forbidden (anti-enumeration)."""
        code, data = self._get("/api/v1/enrollments/99999", user=self.user_student_a)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_10_faculty_accesses_enrollment_detail_success(self):
        """10. FACULTY accesses enrollment detail -> 200 OK."""
        code, data = self._get("/api/v1/enrollments/1", user=self.user_faculty)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 1)

    def test_11_hod_accesses_enrollment_detail_success(self):
        """11. HOD accesses enrollment detail -> 200 OK."""
        code, data = self._get("/api/v1/enrollments/2", user=self.user_hod)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 2)

    def test_12_admin_accesses_enrollment_detail_success(self):
        """12. ADMIN accesses enrollment detail -> 200 OK."""
        code, data = self._get("/api/v1/enrollments/1", user=self.user_admin)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 1)

    def test_13_staff_accesses_nonexistent_enrollment_not_found(self):
        """13. STAFF accesses nonexistent enrollment -> 404 Not Found."""
        code_fac, _ = self._get("/api/v1/enrollments/99999", user=self.user_faculty)
        self.assertEqual(code_fac, 404)
        code_adm, _ = self._get("/api/v1/enrollments/99999", user=self.user_admin)
        self.assertEqual(code_adm, 404)

    # -------------------------------------------------------------------------
    # REGRESSION PRESERVATION
    # -------------------------------------------------------------------------

    def test_14_student_attendance_roster_forbidden_regression(self):
        """14. Student attendance roster remains 403 Forbidden."""
        code, _ = self._get("/api/v1/attendance/", user=self.user_student_a)
        self.assertEqual(code, 403)

    def test_15_student_assessment_roster_forbidden_regression(self):
        """15. Student assessment roster remains 403 Forbidden."""
        code, _ = self._get("/api/v1/assessments/", user=self.user_student_a)
        self.assertEqual(code, 403)

    def test_16_student_attendance_detail_own_success_regression(self):
        """16. Student attendance detail (own) remains 200 OK."""
        code, data = self._get("/api/v1/attendance/101", user=self.user_student_a)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 101)

    def test_17_student_assessment_detail_own_success_regression(self):
        """17. Student assessment detail (own) remains 200 OK."""
        code, data = self._get("/api/v1/assessments/201", user=self.user_student_a)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 201)


if __name__ == "__main__":
    unittest.main()
