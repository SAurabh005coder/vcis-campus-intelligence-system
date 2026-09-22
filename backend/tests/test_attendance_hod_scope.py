"""
VCIS 3.0 — Attendance Directory HOD Department Scope Security Tests

Validates:
1. HOD with department 1 sees Attendance records for students in department 1.
2. HOD with department 1 does NOT see Attendance records for students in department 2.
3. HOD with department 2 sees Attendance records for students in department 2.
4. HOD with multiple students and multiple Attendance records receives only records from their department.
5. HOD with no Faculty profile receives 403 Forbidden.
6. HOD with Faculty profile but department_id=None receives 403 Forbidden.
7. HOD cannot bypass scope using student_id query parameters (e.g. ?student_id=outside_id).
8. HOD cannot bypass scope using enrollment_id query parameters (e.g. ?enrollment_id=outside_id).
9. HOD cannot bypass scope using any existing Attendance filters (e.g. ?department_id=2, ?status=present).
10. ADMIN retains institutional/global Attendance directory access (all departments).
11. FACULTY retains existing institutional/global Attendance directory access (all departments).
12. STUDENT remains denied from the general Attendance directory -> 403 Forbidden.
13. Unauthenticated request remains 401 Unauthorized.
14. Existing Attendance query/filter behavior continues to work within HOD scope.
15. Existing Attendance detail endpoint behavior remains unchanged across roles.
16. Direct security test: HOD cannot retrieve outside-department Attendance records through any parameter combination.
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
os.environ["JWT_SECRET_KEY"] = "test-attendance-hod-scope-secret-key-12345"

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

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.models.attendance import Attendance, AttendanceStatus
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User, UserRole


class TestAttendanceHodScope(unittest.TestCase):
    """Test suite verifying department-scoped attendance directory access for HOD users."""

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

        # 1. Departments, Courses, Subjects
        self.dept_1 = Department(id=1, name="Computer Science and Engineering", code="CSE", is_active=True)
        self.dept_2 = Department(id=2, name="Electronics and Communication", code="ECE", is_active=True)
        self.course_1 = Course(id=1, department_id=1, name="B.Tech CSE", code="BTCSE", duration_years=4, total_semesters=8, is_active=True)
        self.course_2 = Course(id=2, department_id=2, name="B.Tech ECE", code="BTECE", duration_years=4, total_semesters=8, is_active=True)
        self.subject_1 = Subject(id=101, course_id=1, name="Data Structures", code="CS101", semester=1, credits=4)
        self.subject_2 = Subject(id=201, course_id=2, name="Digital Electronics", code="EC201", semester=1, credits=4)
        self.db.add_all([self.dept_1, self.dept_2, self.course_1, self.course_2, self.subject_1, self.subject_2])

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
        # Dept 1 Students
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
        # Dept 2 Students
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

        # 5. Enrollments across Departments
        self.enrollment_d1_a = Enrollment(
            id=1,
            student_id=self.student_d1_a.id,
            subject_id=self.subject_1.id,
            academic_year="2023-24",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment_d1_b = Enrollment(
            id=2,
            student_id=self.student_d1_b.id,
            subject_id=self.subject_1.id,
            academic_year="2023-24",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment_d2_a = Enrollment(
            id=3,
            student_id=self.student_d2_a.id,
            subject_id=self.subject_2.id,
            academic_year="2023-24",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment_d2_b = Enrollment(
            id=4,
            student_id=self.student_d2_b.id,
            subject_id=self.subject_2.id,
            academic_year="2023-24",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add_all([
            self.enrollment_d1_a,
            self.enrollment_d1_b,
            self.enrollment_d2_a,
            self.enrollment_d2_b,
        ])
        self.db.commit()

        # 6. Attendance records across Departments
        # Dept 1 Attendance records
        self.att_d1_a = Attendance(
            id=1,
            enrollment_id=self.enrollment_d1_a.id,
            attendance_date=date(2023, 10, 1),
            status=AttendanceStatus.PRESENT,
            remarks="Alice present",
        )
        self.att_d1_b = Attendance(
            id=2,
            enrollment_id=self.enrollment_d1_b.id,
            attendance_date=date(2023, 10, 1),
            status=AttendanceStatus.ABSENT,
            remarks="Bob absent",
        )
        # Dept 2 Attendance records
        self.att_d2_a = Attendance(
            id=3,
            enrollment_id=self.enrollment_d2_a.id,
            attendance_date=date(2023, 10, 1),
            status=AttendanceStatus.PRESENT,
            remarks="Charlie present",
        )
        self.att_d2_b = Attendance(
            id=4,
            enrollment_id=self.enrollment_d2_b.id,
            attendance_date=date(2023, 10, 1),
            status=AttendanceStatus.PRESENT,
            remarks="Diana present",
        )
        self.db.add_all([
            self.att_d1_a,
            self.att_d1_b,
            self.att_d2_a,
            self.att_d2_b,
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

    def test_01_hod_dept1_sees_only_dept1_attendance(self):
        """1. HOD with department 1 sees Attendance records for students in department 1."""
        status, data = self._get("/api/v1/attendance/", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        att_ids = {a["id"] for a in data}
        self.assertEqual(att_ids, {1, 2})
        enrollment_ids = {a["enrollment_id"] for a in data}
        self.assertEqual(enrollment_ids, {self.enrollment_d1_a.id, self.enrollment_d1_b.id})

    def test_02_hod_dept1_does_not_see_dept2_attendance(self):
        """2. HOD with department 1 does NOT see Attendance records for students in department 2."""
        status, data = self._get("/api/v1/attendance/", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        att_ids = {a["id"] for a in data}
        self.assertNotIn(3, att_ids)
        self.assertNotIn(4, att_ids)
        enrollment_ids = {a["enrollment_id"] for a in data}
        self.assertNotIn(self.enrollment_d2_a.id, enrollment_ids)
        self.assertNotIn(self.enrollment_d2_b.id, enrollment_ids)

    def test_03_hod_dept2_sees_only_dept2_attendance(self):
        """3. HOD with department 2 sees Attendance records for students in department 2."""
        status, data = self._get("/api/v1/attendance/", user=self.user_hod_dept2)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        att_ids = {a["id"] for a in data}
        self.assertEqual(att_ids, {3, 4})
        enrollment_ids = {a["enrollment_id"] for a in data}
        self.assertEqual(enrollment_ids, {self.enrollment_d2_a.id, self.enrollment_d2_b.id})

    def test_04_hod_multiple_records_only_receives_department_attendance(self):
        """4. HOD with multiple students/records only receives records from their department."""
        status, data = self._get("/api/v1/attendance/", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        for a in data:
            # Trace Attendance -> Enrollment -> Student -> department_id
            enrollment = self.db.query(Enrollment).filter(Enrollment.id == a["enrollment_id"]).first()
            student = self.db.query(Student).filter(Student.id == enrollment.student_id).first()
            self.assertEqual(student.department_id, self.dept_1.id)

    def test_05_hod_with_no_faculty_profile_receives_403(self):
        """5. HOD with no Faculty profile receives 403 Forbidden."""
        status, data = self._get("/api/v1/attendance/", user=self.user_hod_orphan)
        self.assertEqual(status, 403)
        self.assertIn("faculty profile", data.get("detail", "").lower())

    def test_06_hod_with_faculty_profile_null_department_receives_403(self):
        """6. HOD with Faculty profile but department_id=None receives 403 Forbidden."""
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

    def test_07_hod_cannot_bypass_scope_using_student_id_query_parameter(self):
        """7. HOD cannot bypass scope using student_id query parameters (e.g. ?student_id=201)."""
        status, data = self._get(f"/api/v1/attendance/?student_id={self.student_d2_a.id}", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        # Still strictly returns dept 1 attendance records
        for a in data:
            self.assertIn(a["id"], [1, 2])

    def test_08_hod_cannot_bypass_scope_using_enrollment_id_query_parameter(self):
        """8. HOD cannot bypass scope using enrollment_id query parameters (e.g. ?enrollment_id=3)."""
        status, data = self._get(f"/api/v1/attendance/?enrollment_id={self.enrollment_d2_a.id}", user=self.user_hod_dept1)
        self.assertEqual(status, 200)
        for a in data:
            self.assertIn(a["id"], [1, 2])

    def test_09_hod_cannot_bypass_scope_using_any_existing_filters(self):
        """9. HOD cannot bypass scope using existing filters (e.g. ?department_id=2, ?status=present)."""
        status, data = self._get(
            f"/api/v1/attendance/?department_id={self.dept_2.id}&status=present&date=2023-10-01",
            user=self.user_hod_dept1,
        )
        self.assertEqual(status, 200)
        for a in data:
            self.assertIn(a["id"], [1, 2])

    def test_10_admin_retains_institutional_global_attendance_access(self):
        """10. ADMIN retains institutional/global Attendance access (all 4 records)."""
        status, data = self._get("/api/v1/attendance/", user=self.user_admin)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        att_ids = {a["id"] for a in data}
        self.assertEqual(att_ids, {1, 2, 3, 4})

    def test_11_faculty_retains_institutional_global_attendance_access(self):
        """11. FACULTY retains existing institutional/global Attendance access (all 4 records)."""
        status, data = self._get("/api/v1/attendance/", user=self.user_faculty)
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        att_ids = {a["id"] for a in data}
        self.assertEqual(att_ids, {1, 2, 3, 4})

    def test_12_student_remains_denied_from_general_attendance_directory(self):
        """12. STUDENT remains denied from general Attendance directory -> 403 Forbidden."""
        status, data = self._get("/api/v1/attendance/", user=self.user_student_1)
        self.assertEqual(status, 403)
        self.assertIn("detail", data)

    def test_13_unauthenticated_request_remains_401(self):
        """13. Unauthenticated request remains 401 Unauthorized."""
        status, data = self._get("/api/v1/attendance/", user=None)
        self.assertEqual(status, 401)

    def test_14_existing_attendance_query_filters_work_within_hod_scope(self):
        """14. Existing Attendance query/filter behavior continues to work within HOD scope."""
        status, data = self._get(
            "/api/v1/attendance/?limit=10&offset=0",
            user=self.user_hod_dept1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 2)
        for a in data:
            self.assertIn(a["id"], [1, 2])

    def test_15_attendance_detail_endpoint_behavior_remains_intact(self):
        """15. Existing Attendance detail endpoint behavior remains unchanged across roles."""
        # Admin accesses detail -> 200
        status_admin, data_admin = self._get(f"/api/v1/attendance/{self.att_d1_a.id}", user=self.user_admin)
        self.assertEqual(status_admin, 200)
        self.assertEqual(data_admin["id"], self.att_d1_a.id)

        # Faculty accesses detail -> 200
        status_fac, data_fac = self._get(f"/api/v1/attendance/{self.att_d1_a.id}", user=self.user_faculty)
        self.assertEqual(status_fac, 200)
        self.assertEqual(data_fac["id"], self.att_d1_a.id)

        # Student 1 accesses own attendance -> 200
        status_s1, data_s1 = self._get(f"/api/v1/attendance/{self.att_d1_a.id}", user=self.user_student_1)
        self.assertEqual(status_s1, 200)
        self.assertEqual(data_s1["id"], self.att_d1_a.id)

        # Student 1 accesses other student's attendance -> 403 Forbidden
        status_other, _ = self._get(f"/api/v1/attendance/{self.att_d2_a.id}", user=self.user_student_1)
        self.assertEqual(status_other, 403)

    def test_16_security_hod_cannot_retrieve_outside_department_attendance(self):
        """16. Security Test: HOD cannot retrieve outside-department Attendance records via any parameter combination."""
        # Outside attendance record is id=3 (student_d2_a, enrollment_d2_a)
        status, data = self._get(
            f"/api/v1/attendance/?student_id={self.student_d2_a.id}&enrollment_id={self.enrollment_d2_a.id}&department_id={self.dept_2.id}",
            user=self.user_hod_dept1,
        )
        self.assertEqual(status, 200)
        returned_ids = {a["id"] for a in data}
        self.assertNotIn(self.att_d2_a.id, returned_ids)
        self.assertNotIn(self.att_d2_b.id, returned_ids)
        for a in data:
            self.assertIn(a["id"], [1, 2])


if __name__ == "__main__":
    unittest.main()
