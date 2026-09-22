"""
VCIS 3.0 — Attendance & Assessment Roster Exposure Security Tests

Validates:
1. STUDENT GET /api/v1/attendance/ is blocked with HTTP 403 Forbidden.
2. STUDENT cannot bypass attendance roster restriction using query parameters.
3. FACULTY GET /api/v1/attendance/ returns HTTP 200 with attendance records.
4. HOD GET /api/v1/attendance/ returns HTTP 200 with attendance records.
5. ADMIN GET /api/v1/attendance/ returns HTTP 200 with attendance records.
6. STUDENT GET /api/v1/assessments/ is blocked with HTTP 403 Forbidden.
7. STUDENT cannot bypass assessment roster restriction using query parameters.
8. FACULTY GET /api/v1/assessments/ returns HTTP 200 with assessment records.
9. HOD GET /api/v1/assessments/ returns HTTP 200 with assessment records.
10. ADMIN GET /api/v1/assessments/ returns HTTP 200 with assessment records.
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
os.environ["JWT_SECRET_KEY"] = "test-security-att-ass-secret-key-12345"

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


class TestAttendanceAssessmentSecurity(unittest.TestCase):
    """Test suite verifying authorization rules on attendance and assessment list endpoints."""

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

        # Users
        self.user_student = User(
            id=1,
            email="student@test.com",
            password_hash="pw_stud",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_faculty = User(
            id=2,
            email="faculty@test.com",
            password_hash="pw_fac",
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_hod = User(
            id=3,
            email="hod@test.com",
            password_hash="pw_hod",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_admin = User(
            id=4,
            email="admin@test.com",
            password_hash="pw_adm",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.db.add_all([
            self.user_student,
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

        # Student & Enrollment
        self.student = Student(
            id=10,
            user_id=1,
            department_id=1,
            course_id=1,
            roll_number="23MCA001",
            admission_year=2023,
            current_semester=1,
            name="Alice Student",
            email="student@test.com",
            is_active=True,
        )
        self.enrollment = Enrollment(
            id=1,
            student_id=10,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add_all([self.student, self.enrollment])

        # Attendance & Assessment records
        self.att_record = Attendance(
            id=1,
            enrollment_id=1,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
            remarks="Regular class",
        )
        self.ass_record = Assessment(
            id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1",
            max_marks=50,
            obtained_marks=42,
            assessment_date=date(2023, 9, 20),
            remarks="Good performance",
        )
        self.db.add_all([self.att_record, self.ass_record])
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
    # ATTENDANCE TESTS
    # ==================================================================

    def test_01_student_get_attendance_is_blocked(self):
        """TEST 1: STUDENT GET /api/v1/attendance/ -> HTTP 403 Forbidden."""
        status, data = self._get(
            "/api/v1/attendance/",
            user=self.user_student,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_02_student_cannot_bypass_attendance_with_query_params(self):
        """TEST 2: STUDENT cannot bypass attendance restriction with query parameters."""
        status, data = self._get(
            "/api/v1/attendance/?enrollment_id=1&student_id=10&status=present",
            user=self.user_student,
        )
        self.assertEqual(status, 403)

    def test_03_faculty_get_attendance_succeeds(self):
        """TEST 3: FACULTY GET /api/v1/attendance/ -> HTTP 200 OK."""
        status, data = self._get(
            "/api/v1/attendance/",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["enrollment_id"], 1)

    def test_04_hod_get_attendance_succeeds(self):
        """TEST 4: HOD GET /api/v1/attendance/ -> HTTP 200 OK."""
        status, data = self._get(
            "/api/v1/attendance/",
            user=self.user_hod,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_05_admin_get_attendance_succeeds(self):
        """TEST 5: ADMIN GET /api/v1/attendance/ -> HTTP 200 OK."""
        status, data = self._get(
            "/api/v1/attendance/",
            user=self.user_admin,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    # ==================================================================
    # ASSESSMENT TESTS
    # ==================================================================

    def test_06_student_get_assessments_is_blocked(self):
        """TEST 6: STUDENT GET /api/v1/assessments/ -> HTTP 403 Forbidden."""
        status, data = self._get(
            "/api/v1/assessments/",
            user=self.user_student,
        )
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_07_student_cannot_bypass_assessments_with_query_params(self):
        """TEST 7: STUDENT cannot bypass assessment restriction with query parameters."""
        status, data = self._get(
            "/api/v1/assessments/?enrollment_id=1&assessment_type=ct1",
            user=self.user_student,
        )
        self.assertEqual(status, 403)

    def test_08_faculty_get_assessments_succeeds(self):
        """TEST 8: FACULTY GET /api/v1/assessments/ -> HTTP 200 OK."""
        status, data = self._get(
            "/api/v1/assessments/",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["enrollment_id"], 1)

    def test_09_hod_get_assessments_succeeds(self):
        """TEST 9: HOD GET /api/v1/assessments/ -> HTTP 200 OK."""
        status, data = self._get(
            "/api/v1/assessments/",
            user=self.user_hod,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    def test_10_admin_get_assessments_succeeds(self):
        """TEST 10: ADMIN GET /api/v1/assessments/ -> HTTP 200 OK."""
        status, data = self._get(
            "/api/v1/assessments/",
            user=self.user_admin,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)


if __name__ == "__main__":
    unittest.main()
