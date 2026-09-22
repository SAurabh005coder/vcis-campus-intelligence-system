"""
VCIS 3.0 — Results Detail Endpoints HOD Department Scope Security Tests

Validates:
1. HOD can access enrollment result belonging to own department.
2. HOD cannot access enrollment result belonging to another department -> 403 Forbidden.
3. HOD can access own-department student summary.
4. HOD cannot access another-department student summary -> 403 Forbidden.
5. HOD can access own-department semester result.
6. HOD cannot access another-department semester result -> 403 Forbidden.
7. HOD can access own-department enrollment performance.
8. HOD cannot access another-department enrollment performance -> 403 Forbidden.
9. HOD without Faculty profile receives 403 Forbidden on detail endpoints.
10. HOD with Faculty profile but department_id=None receives 403 Forbidden.
11. ADMIN retains access to results across departments (HTTP 200).
12. FACULTY retains access to results across departments (HTTP 200).
13. STUDENT's existing ownership behavior remains unchanged (own records -> HTTP 200).
14. STUDENT cannot access another student's result -> HTTP 403 Forbidden.
15. Unauthenticated requests remain 401 Unauthorized.
16. Nonexistent enrollment/student behavior remains consistent (HTTP 404 Not Found).
17. Direct cross-department enrollment_id attack is rejected (HTTP 403 Forbidden).
18. Direct cross-department student_id attack is rejected (HTTP 403 Forbidden).
19. Existing result calculation output for authorized requests remains unchanged.
20. Existing result security regression tests continue to pass.
"""

import asyncio
from datetime import date
import json
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-results-detail-hod-scope-secret-key-12345"

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


class TestResultsHodDetailScope(unittest.TestCase):
    """Test suite verifying HOD department scoping for all Results detail endpoints."""

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

        # -------------------------------------------------------------
        # 1. Departments
        # -------------------------------------------------------------
        self.dept_a = Department(id=1, name="Department A", code="DEPTA")
        self.dept_b = Department(id=2, name="Department B", code="DEPTB")
        self.db.add_all([self.dept_a, self.dept_b])

        # -------------------------------------------------------------
        # 2. Courses
        # -------------------------------------------------------------
        self.course_a = Course(
            id=1,
            department_id=1,
            name="Course A",
            code="CA",
            duration_years=2,
            total_semesters=4,
        )
        self.course_b = Course(
            id=2,
            department_id=2,
            name="Course B",
            code="CB",
            duration_years=2,
            total_semesters=4,
        )
        self.db.add_all([self.course_a, self.course_b])

        # -------------------------------------------------------------
        # 3. Subjects
        # -------------------------------------------------------------
        self.subject_a = Subject(
            id=101,
            course_id=1,
            name="Subject A1",
            code="SA1",
            semester=1,
            credits=4,
        )
        self.subject_b = Subject(
            id=201,
            course_id=2,
            name="Subject B1",
            code="SB1",
            semester=1,
            credits=4,
        )
        self.db.add_all([self.subject_a, self.subject_b])

        # -------------------------------------------------------------
        # 4. Users
        # -------------------------------------------------------------
        self.user_hod_a = User(
            id=10,
            email="hod_a@test.com",
            password_hash="pw_hoda",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_hod_b = User(
            id=11,
            email="hod_b@test.com",
            password_hash="pw_hodb",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_hod_unassigned = User(
            id=12,
            email="hod_unassigned@test.com",
            password_hash="pw_hodun",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_faculty = User(
            id=14,
            email="faculty@test.com",
            password_hash="pw_fac",
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_admin = User(
            id=15,
            email="admin@test.com",
            password_hash="pw_adm",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.user_student_a = User(
            id=1,
            email="student_a@test.com",
            password_hash="pw_sa",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_student_b = User(
            id=2,
            email="student_b@test.com",
            password_hash="pw_sb",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add_all([
            self.user_hod_a,
            self.user_hod_b,
            self.user_hod_unassigned,
            self.user_faculty,
            self.user_admin,
            self.user_student_a,
            self.user_student_b,
        ])

        # -------------------------------------------------------------
        # 5. Faculty Profiles
        # -------------------------------------------------------------
        self.faculty_hod_a = Faculty(
            id=1,
            user_id=10,
            department_id=1,
            employee_code="HOD-A-001",
            first_name="Dr.",
            last_name="HOD A",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_hod_b = Faculty(
            id=2,
            user_id=11,
            department_id=2,
            employee_code="HOD-B-001",
            first_name="Dr.",
            last_name="HOD B",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_regular = Faculty(
            id=4,
            user_id=14,
            department_id=1,
            employee_code="FAC-A-001",
            first_name="Prof.",
            last_name="Regular",
            designation="Assistant Professor",
            is_active=True,
        )
        self.db.add_all([
            self.faculty_hod_a,
            self.faculty_hod_b,
            self.faculty_regular,
        ])

        # -------------------------------------------------------------
        # 6. Student Profiles
        # -------------------------------------------------------------
        self.student_a = Student(
            id=101,
            user_id=1,
            department_id=1,
            course_id=1,
            roll_number="23DEPTA001",
            admission_year=2023,
            current_semester=1,
            name="Alice DeptA",
            email="student_a@test.com",
            is_active=True,
        )
        self.student_b = Student(
            id=201,
            user_id=2,
            department_id=2,
            course_id=2,
            roll_number="23DEPTB001",
            admission_year=2023,
            current_semester=1,
            name="Bob DeptB",
            email="student_b@test.com",
            is_active=True,
        )
        self.db.add_all([self.student_a, self.student_b])

        # -------------------------------------------------------------
        # 7. Enrollments
        # -------------------------------------------------------------
        self.enrollment_a = Enrollment(
            id=501,
            student_id=101,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment_b = Enrollment(
            id=601,
            student_id=201,
            subject_id=201,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add_all([self.enrollment_a, self.enrollment_b])

        # -------------------------------------------------------------
        # 8. Assessments
        # -------------------------------------------------------------
        self.assessment_a = Assessment(
            id=701,
            enrollment_id=501,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1 A",
            max_marks=50.0,
            obtained_marks=45.0,
            assessment_date=date(2023, 9, 20),
        )
        self.assessment_b = Assessment(
            id=801,
            enrollment_id=601,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1 B",
            max_marks=50.0,
            obtained_marks=35.0,
            assessment_date=date(2023, 9, 20),
        )
        self.db.add_all([self.assessment_a, self.assessment_b])

        # -------------------------------------------------------------
        # 9. Attendance
        # -------------------------------------------------------------
        self.att_a = Attendance(
            id=901,
            enrollment_id=501,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
        )
        self.att_b = Attendance(
            id=902,
            enrollment_id=601,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
        )
        self.db.add_all([self.att_a, self.att_b])

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
    ) -> tuple[int, dict | list]:
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

        parsed_path = path
        query_string = b""
        if "?" in path:
            parsed_path, qs = path.split("?", 1)
            query_string = qs.encode("ascii")

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method.upper(),
            "path": parsed_path,
            "raw_path": path.encode("ascii"),
            "query_string": query_string,
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

    def test_01_hod_can_access_own_department_enrollment_result(self):
        """1. HOD can access enrollment result belonging to own department."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["enrollment_id"], self.enrollment_a.id)
        self.assertEqual(data["student_id"], self.student_a.id)

    def test_02_hod_cannot_access_another_department_enrollment_result(self):
        """2. HOD cannot access enrollment result belonging to another department -> 403."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_03_hod_can_access_own_department_student_summary(self):
        """3. HOD can access own-department student summary."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)
        self.assertEqual(data["total_subjects"], 1)

    def test_04_hod_cannot_access_another_department_student_summary(self):
        """4. HOD cannot access another-department student summary -> 403."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_b.id}/summary",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_05_hod_can_access_own_department_semester_result(self):
        """5. HOD can access own-department semester result."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)
        self.assertEqual(data["semester"], 1)

    def test_06_hod_cannot_access_another_department_semester_result(self):
        """6. HOD cannot access another-department semester result -> 403."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_b.id}/semester/1",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_07_hod_can_access_own_department_enrollment_performance(self):
        """7. HOD can access own-department enrollment performance."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["enrollment_id"], self.enrollment_a.id)

    def test_08_hod_cannot_access_another_department_enrollment_performance(self):
        """8. HOD cannot access another-department enrollment performance -> 403."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}/performance",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_09_hod_without_faculty_profile_receives_403(self):
        """9. HOD without Faculty profile receives 403 on all detail endpoints."""
        endpoints = [
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
        ]
        for ep in endpoints:
            status, data = self._request("GET", ep, user=self.user_hod_unassigned)
            self.assertEqual(status, 403, f"Expected 403 for {ep}")
            self.assertIn("faculty profile", data.get("detail", "").lower())

    def test_10_hod_with_faculty_profile_null_department_receives_403(self):
        """10. HOD with Faculty profile but department_id=None receives 403 Forbidden."""
        from app.core.authorization import resolve_hod_department_id
        from fastapi import HTTPException

        mock_faculty = Faculty(
            id=99,
            user_id=self.user_hod_unassigned.id,
            department_id=1,
            employee_code="HOD-NULL-001",
            first_name="Null",
            last_name="Dept",
            designation="HOD Unassigned",
        )
        mock_faculty.department_id = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_faculty

        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_hod_unassigned, mock_db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("assigned department", ctx.exception.detail.lower())

    def test_11_admin_retains_access_across_departments(self):
        """11. ADMIN retains access to results across departments (HTTP 200)."""
        endpoints = [
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            f"/api/v1/results/student/{self.student_b.id}/summary",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            f"/api/v1/results/student/{self.student_b.id}/semester/1",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}/performance",
        ]
        for ep in endpoints:
            status, _ = self._request("GET", ep, user=self.user_admin)
            self.assertEqual(status, 200, f"Admin failed on {ep}")

    def test_12_faculty_retains_access_across_departments(self):
        """12. FACULTY retains access to results across departments (HTTP 200)."""
        endpoints = [
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            f"/api/v1/results/student/{self.student_b.id}/summary",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            f"/api/v1/results/student/{self.student_b.id}/semester/1",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}/performance",
        ]
        for ep in endpoints:
            status, _ = self._request("GET", ep, user=self.user_faculty)
            self.assertEqual(status, 200, f"Faculty failed on {ep}")

    def test_13_student_ownership_behavior_remains_unchanged(self):
        """13. STUDENT's existing ownership behavior remains unchanged (own records -> 200)."""
        own_endpoints = [
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
        ]
        for ep in own_endpoints:
            status, _ = self._request("GET", ep, user=self.user_student_a)
            self.assertEqual(status, 200, f"Student A failed on own endpoint {ep}")

    def test_14_student_cannot_access_another_students_result(self):
        """14. STUDENT cannot access another student's result -> HTTP 403 Forbidden."""
        other_endpoints = [
            f"/api/v1/results/enrollment/{self.enrollment_b.id}",
            f"/api/v1/results/student/{self.student_b.id}/summary",
            f"/api/v1/results/student/{self.student_b.id}/semester/1",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}/performance",
        ]
        for ep in other_endpoints:
            status, _ = self._request("GET", ep, user=self.user_student_a)
            self.assertEqual(status, 403, f"Student A should be denied on {ep}")

    def test_15_unauthenticated_requests_remain_401(self):
        """15. Unauthenticated requests remain 401 Unauthorized."""
        endpoints = [
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
        ]
        for ep in endpoints:
            status, _ = self._request("GET", ep, user=None)
            self.assertEqual(status, 401, f"Expected 401 on {ep}")

    def test_16_nonexistent_enrollment_student_behavior(self):
        """16. Nonexistent enrollment/student behavior remains consistent (HTTP 404 Not Found)."""
        # Nonexistent enrollment -> 404
        status, _ = self._request("GET", "/api/v1/results/enrollment/99999", user=self.user_hod_a)
        self.assertEqual(status, 404)

        status, _ = self._request("GET", "/api/v1/results/enrollment/99999/performance", user=self.user_hod_a)
        self.assertEqual(status, 404)

        # Nonexistent student -> 404
        status, _ = self._request("GET", "/api/v1/results/student/99999/summary", user=self.user_hod_a)
        self.assertEqual(status, 404)

        status, _ = self._request("GET", "/api/v1/results/student/99999/semester/1", user=self.user_hod_a)
        self.assertEqual(status, 404)

    def test_17_direct_cross_department_enrollment_id_attack(self):
        """17. Direct cross-department enrollment_id attack is rejected (HTTP 403 Forbidden)."""
        # HOD A attempts to fetch Enrollment B result
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

        # HOD B attempts to fetch Enrollment A result
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            user=self.user_hod_b,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_18_direct_cross_department_student_id_attack(self):
        """18. Direct cross-department student_id attack is rejected (HTTP 403 Forbidden)."""
        # HOD A attempts to fetch Student B summary and semester result
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_b.id}/summary",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_b.id}/semester/1",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

        # HOD B attempts to fetch Student A summary and semester result
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/summary",
            user=self.user_hod_b,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student_a.id}/semester/1",
            user=self.user_hod_b,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_19_existing_result_calculation_output_remains_unchanged(self):
        """19. Existing result calculation output for authorized requests remains unchanged."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["enrollment_id"], 501)
        self.assertEqual(data["total_max_marks"], 50)
        self.assertEqual(data["total_obtained_marks"], 45)
        self.assertEqual(data["overall_percentage"], 90.0)
        self.assertEqual(len(data["assessments"]), 1)
        self.assertEqual(data["assessments"][0]["percentage"], 90.0)

    def test_20_existing_result_security_regression_tests_continue_to_pass(self):
        """20. Both HOD A and HOD B can access own department records without cross-access."""
        # HOD A -> Enrollment A performance
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_a.id}/performance",
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["enrollment_id"], 501)
        self.assertEqual(data["student_id"], 101)

        # HOD B -> Enrollment B performance
        status, data = self._request(
            "GET",
            f"/api/v1/results/enrollment/{self.enrollment_b.id}/performance",
            user=self.user_hod_b,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["enrollment_id"], 601)
        self.assertEqual(data["student_id"], 201)


if __name__ == "__main__":
    unittest.main()
