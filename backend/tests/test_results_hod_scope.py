"""
VCIS 3.0 — Results Directory HOD Department Scope Security Tests

Validates:
1. HOD with department 1 sees results for students in department 1.
2. HOD with department 1 does NOT see results for students in department 2.
3. HOD with department 2 sees results for students in department 2.
4. HOD with multiple students/results receives only results from their department.
5. HOD with no Faculty profile receives 403 Forbidden.
6. HOD with Faculty profile but department_id=None receives 403 Forbidden.
7. HOD cannot bypass scope using student_id query parameters (e.g. ?student_id=outside_id).
8. HOD cannot bypass scope using enrollment_id query parameters (e.g. ?enrollment_id=outside_id).
9. HOD cannot bypass scope using subject_id query parameters (e.g. ?subject_id=201).
10. HOD cannot bypass scope using course_id query parameters (e.g. ?course_id=2).
11. HOD cannot bypass scope using semester filters (e.g. ?semester=1).
12. ADMIN retains institutional/global Result access (all departments).
13. FACULTY retains existing institutional/global Result access (all departments).
14. STUDENT remains denied from the general Results directory -> 403 Forbidden.
15. Unauthenticated request remains 401 Unauthorized.
16. Existing result filtering/calculation behavior continues to work within HOD scope.
17. Existing Result detail endpoint behavior remains unchanged across roles.
18. Direct security test: HOD cannot obtain an outside-department result through any supported query parameter combination.
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
os.environ["JWT_SECRET_KEY"] = "test-results-hod-scope-secret-key-12345"

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


class TestResultsHodScope(unittest.TestCase):
    """Test suite verifying HOD department scoping for GET /api/v1/results/."""

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
        self.dept1 = Department(id=1, name="Computer Science", code="CS")
        self.dept2 = Department(id=2, name="Mechanical Engineering", code="ME")
        self.db.add_all([self.dept1, self.dept2])

        # -------------------------------------------------------------
        # 2. Courses
        # -------------------------------------------------------------
        self.course1 = Course(
            id=1,
            department_id=1,
            name="MCA",
            code="MCA",
            duration_years=2,
            total_semesters=4,
        )
        self.course2 = Course(
            id=2,
            department_id=2,
            name="M.Tech ME",
            code="MME",
            duration_years=2,
            total_semesters=4,
        )
        self.db.add_all([self.course1, self.course2])

        # -------------------------------------------------------------
        # 3. Subjects
        # -------------------------------------------------------------
        self.subject1 = Subject(
            id=101,
            course_id=1,
            name="Data Structures",
            code="CS101",
            semester=1,
            credits=4,
        )
        self.subject2 = Subject(
            id=201,
            course_id=2,
            name="Thermodynamics",
            code="ME201",
            semester=1,
            credits=4,
        )
        self.db.add_all([self.subject1, self.subject2])

        # -------------------------------------------------------------
        # 4. Users
        # -------------------------------------------------------------
        self.user_hod1 = User(
            id=10,
            email="hod_cs@test.com",
            password_hash="pw_hod1",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_hod2 = User(
            id=11,
            email="hod_me@test.com",
            password_hash="pw_hod2",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_hod_unassigned = User(
            id=12,
            email="hod_unassigned@test.com",
            password_hash="pw_hod_un",
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
        self.user_student1 = User(
            id=1,
            email="student1@test.com",
            password_hash="pw_s1",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_student2 = User(
            id=2,
            email="student2@test.com",
            password_hash="pw_s2",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_student3 = User(
            id=3,
            email="student3@test.com",
            password_hash="pw_s3",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_student4 = User(
            id=4,
            email="student4@test.com",
            password_hash="pw_s4",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add_all([
            self.user_hod1,
            self.user_hod2,
            self.user_hod_unassigned,
            self.user_faculty,
            self.user_admin,
            self.user_student1,
            self.user_student2,
            self.user_student3,
            self.user_student4,
        ])

        # -------------------------------------------------------------
        # 5. Faculty Profiles
        # -------------------------------------------------------------
        self.faculty_hod1 = Faculty(
            id=1,
            user_id=10,
            department_id=1,
            employee_code="HOD-CS-001",
            first_name="Dr.",
            last_name="CS HOD",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_hod2 = Faculty(
            id=2,
            user_id=11,
            department_id=2,
            employee_code="HOD-ME-001",
            first_name="Dr.",
            last_name="ME HOD",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_regular = Faculty(
            id=4,
            user_id=14,
            department_id=1,
            employee_code="FAC-CS-001",
            first_name="Prof.",
            last_name="Regular",
            designation="Assistant Professor",
            is_active=True,
        )
        self.db.add_all([
            self.faculty_hod1,
            self.faculty_hod2,
            self.faculty_regular,
        ])

        # -------------------------------------------------------------
        # 6. Student Profiles
        # Dept 1: Student 1 & 2
        # Dept 2: Student 3 & 4
        # -------------------------------------------------------------
        self.student1 = Student(
            id=101,
            user_id=1,
            department_id=1,
            course_id=1,
            roll_number="23CS001",
            admission_year=2023,
            current_semester=1,
            name="Alice CS",
            email="student1@test.com",
            is_active=True,
        )
        self.student2 = Student(
            id=102,
            user_id=2,
            department_id=1,
            course_id=1,
            roll_number="23CS002",
            admission_year=2023,
            current_semester=1,
            name="Bob CS",
            email="student2@test.com",
            is_active=True,
        )
        self.student3 = Student(
            id=201,
            user_id=3,
            department_id=2,
            course_id=2,
            roll_number="23ME001",
            admission_year=2023,
            current_semester=1,
            name="Charlie ME",
            email="student3@test.com",
            is_active=True,
        )
        self.student4 = Student(
            id=202,
            user_id=4,
            department_id=2,
            course_id=2,
            roll_number="23ME002",
            admission_year=2023,
            current_semester=1,
            name="Diana ME",
            email="student4@test.com",
            is_active=True,
        )
        self.db.add_all([
            self.student1,
            self.student2,
            self.student3,
            self.student4,
        ])

        # -------------------------------------------------------------
        # 7. Enrollments
        # Dept 1: Enrollment 501 (Student 1), 502 (Student 2)
        # Dept 2: Enrollment 601 (Student 3), 602 (Student 4)
        # -------------------------------------------------------------
        self.enrollment1 = Enrollment(
            id=501,
            student_id=101,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment2 = Enrollment(
            id=502,
            student_id=102,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment3 = Enrollment(
            id=601,
            student_id=201,
            subject_id=201,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment4 = Enrollment(
            id=602,
            student_id=202,
            subject_id=201,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add_all([
            self.enrollment1,
            self.enrollment2,
            self.enrollment3,
            self.enrollment4,
        ])

        # -------------------------------------------------------------
        # 8. Assessments
        # -------------------------------------------------------------
        self.assessment1 = Assessment(
            id=701,
            enrollment_id=501,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1 CS",
            max_marks=50.0,
            obtained_marks=45.0,
            assessment_date=date(2023, 9, 20),
        )
        self.assessment2 = Assessment(
            id=702,
            enrollment_id=502,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1 CS",
            max_marks=50.0,
            obtained_marks=40.0,
            assessment_date=date(2023, 9, 20),
        )
        self.assessment3 = Assessment(
            id=801,
            enrollment_id=601,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1 ME",
            max_marks=50.0,
            obtained_marks=35.0,
            assessment_date=date(2023, 9, 20),
        )
        self.assessment4 = Assessment(
            id=802,
            enrollment_id=602,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1 ME",
            max_marks=50.0,
            obtained_marks=30.0,
            assessment_date=date(2023, 9, 20),
        )
        self.db.add_all([
            self.assessment1,
            self.assessment2,
            self.assessment3,
            self.assessment4,
        ])

        # -------------------------------------------------------------
        # 9. Attendance
        # -------------------------------------------------------------
        self.att1 = Attendance(
            id=901,
            enrollment_id=501,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
        )
        self.att2 = Attendance(
            id=902,
            enrollment_id=601,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
        )
        self.db.add_all([self.att1, self.att2])

        self.db.commit()

        # Test client dispatch override
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

    def test_01_hod_dept1_sees_only_dept1_results(self):
        """1. HOD with department 1 sees results for students in department 1."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        student_ids = {r["student_id"] for r in data}
        enrollment_ids = {r["enrollment_id"] for r in data}
        self.assertEqual(student_ids, {101, 102})
        self.assertEqual(enrollment_ids, {501, 502})

    def test_02_hod_dept1_does_not_see_dept2_results(self):
        """2. HOD with department 1 does NOT see results for students in department 2."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        for result in data:
            self.assertNotEqual(result["student_id"], 201)
            self.assertNotEqual(result["student_id"], 202)
            self.assertNotEqual(result["enrollment_id"], 601)
            self.assertNotEqual(result["enrollment_id"], 602)

    def test_03_hod_dept2_sees_only_dept2_results(self):
        """3. HOD with department 2 sees results for students in department 2."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=self.user_hod2,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        student_ids = {r["student_id"] for r in data}
        enrollment_ids = {r["enrollment_id"] for r in data}
        self.assertEqual(student_ids, {201, 202})
        self.assertEqual(enrollment_ids, {601, 602})

    def test_04_hod_multiple_records_only_receives_department_results(self):
        """4. HOD with multiple students/records receives only results from their department."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        for r in data:
            # Check student belongs to Dept 1
            student = self.db.query(Student).filter(Student.id == r["student_id"]).first()
            self.assertIsNotNone(student)
            self.assertEqual(student.department_id, 1)

    def test_05_hod_with_no_faculty_profile_receives_403(self):
        """5. HOD with no Faculty profile receives 403 Forbidden."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=self.user_hod_unassigned,
        )
        self.assertEqual(status, 403)
        self.assertIn("faculty profile", data.get("detail", "").lower())

    def test_06_hod_with_faculty_profile_null_department_receives_403(self):
        """6. HOD with Faculty profile but department_id=None receives 403 Forbidden."""
        from unittest.mock import MagicMock
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

    def test_07_hod_cannot_bypass_scope_using_student_id_query_parameter(self):
        """7. HOD cannot bypass scope using student_id query parameters (e.g. ?student_id=201)."""
        # HOD 1 queries with student_id=201 (student in dept 2) -> empty list
        status, data = self._request(
            "GET",
            f"/api/v1/results/?student_id={self.student3.id}",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data, [])

        # HOD 1 queries with own student_id=101 -> succeeds with 1 record
        status, data = self._request(
            "GET",
            f"/api/v1/results/?student_id={self.student1.id}",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["student_id"], 101)

    def test_08_hod_cannot_bypass_scope_using_enrollment_id_query_parameter(self):
        """8. HOD cannot bypass scope using enrollment_id query parameters (e.g. ?enrollment_id=601)."""
        # HOD 1 queries with enrollment_id=601 (enrollment in dept 2) -> empty list
        status, data = self._request(
            "GET",
            f"/api/v1/results/?enrollment_id={self.enrollment3.id}",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data, [])

        # HOD 1 queries with own enrollment_id=501 -> succeeds
        status, data = self._request(
            "GET",
            f"/api/v1/results/?enrollment_id={self.enrollment1.id}",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["enrollment_id"], 501)

    def test_09_hod_cannot_bypass_scope_using_subject_id_query_parameter(self):
        """9. HOD cannot bypass scope using subject_id query parameters (e.g. ?subject_id=201)."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/?subject_id={self.subject2.id}",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data, [])

    def test_10_hod_cannot_bypass_scope_using_course_id_query_parameter(self):
        """10. HOD cannot bypass scope using course_id query parameters (e.g. ?course_id=2)."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/?course_id={self.course2.id}",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data, [])

    def test_11_hod_cannot_bypass_scope_using_semester_filters(self):
        """11. HOD cannot bypass scope using semester filters."""
        # Both departments have semester 1 subjects. HOD 1 requesting semester=1 must receive only Dept 1
        status, data = self._request(
            "GET",
            "/api/v1/results/?semester=1",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 2)
        for r in data:
            self.assertIn(r["student_id"], {101, 102})

    def test_12_admin_retains_institutional_global_result_access(self):
        """12. ADMIN retains institutional/global Result access (all 4 records)."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=self.user_admin,
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 4)
        enrollment_ids = {r["enrollment_id"] for r in data}
        self.assertEqual(enrollment_ids, {501, 502, 601, 602})

    def test_13_faculty_retains_institutional_global_result_access(self):
        """13. FACULTY retains existing institutional/global Result access (all 4 records)."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 4)
        enrollment_ids = {r["enrollment_id"] for r in data}
        self.assertEqual(enrollment_ids, {501, 502, 601, 602})

    def test_14_student_remains_denied_from_general_results_directory(self):
        """14. STUDENT remains denied from general Results directory -> 403 Forbidden."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=self.user_student1,
        )
        self.assertEqual(status, 403)

    def test_15_unauthenticated_request_remains_401(self):
        """15. Unauthenticated request remains 401 Unauthorized."""
        status, data = self._request(
            "GET",
            "/api/v1/results/",
            user=None,
        )
        self.assertEqual(status, 401)

    def test_16_existing_result_calculation_behavior_works_within_hod_scope(self):
        """16. Existing result calculation behavior continues to work within HOD scope."""
        status, data = self._request(
            "GET",
            f"/api/v1/results/?enrollment_id={self.enrollment1.id}",
            user=self.user_hod1,
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(data), 1)
        res = data[0]
        self.assertEqual(res["enrollment_id"], 501)
        self.assertEqual(res["total_max_marks"], 50)
        self.assertEqual(res["total_obtained_marks"], 45)
        self.assertEqual(res["overall_percentage"], 90.0)
        self.assertEqual(len(res["assessments"]), 1)
        self.assertEqual(res["assessments"][0]["percentage"], 90.0)

    def test_17_result_detail_endpoint_behavior_remains_intact(self):
        """17. Existing Result detail endpoint behavior remains unchanged across roles."""
        # Student 1 accessing own summary -> 200
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student1.id}/summary",
            user=self.user_student1,
        )
        self.assertEqual(status, 200)

        # Student 1 accessing Student 2 summary -> 403
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student2.id}/summary",
            user=self.user_student1,
        )
        self.assertEqual(status, 403)

        # Faculty accessing Student 1 summary -> 200
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student1.id}/summary",
            user=self.user_faculty,
        )
        self.assertEqual(status, 200)

        # Admin accessing Student 3 semester result -> 200
        status, data = self._request(
            "GET",
            f"/api/v1/results/student/{self.student3.id}/semester/1",
            user=self.user_admin,
        )
        self.assertEqual(status, 200)

    def test_18_security_hod_cannot_retrieve_outside_department_result(self):
        """18. Security Test: HOD cannot retrieve outside-department results via any parameter combination."""
        parameter_attacks = [
            f"?student_id={self.student3.id}",
            f"?enrollment_id={self.enrollment3.id}",
            f"?subject_id={self.subject2.id}",
            f"?course_id={self.course2.id}",
            f"?student_id={self.student3.id}&enrollment_id={self.enrollment3.id}",
            f"?student_id={self.student3.id}&subject_id={self.subject2.id}&semester=1",
            f"?enrollment_id={self.enrollment4.id}&course_id={self.course2.id}",
        ]
        for query_params in parameter_attacks:
            status, data = self._request(
                "GET",
                f"/api/v1/results/{query_params}",
                user=self.user_hod1,
            )
            self.assertEqual(status, 200, f"Failed on {query_params}")
            self.assertEqual(data, [], f"Expected empty list for {query_params}, got {data}")


if __name__ == "__main__":
    unittest.main()
