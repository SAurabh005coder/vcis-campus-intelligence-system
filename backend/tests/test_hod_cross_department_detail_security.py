"""
VCIS 3.0 — HOD Cross-Department Detail IDOR Security Tests

Validates comprehensive department scoping on direct detail endpoints:
1. GET /api/v1/students/{student_id}
2. GET /api/v1/enrollments/{enrollment_id}
3. GET /api/v1/attendance/{attendance_id}
4. GET /api/v1/assessments/{assessment_id}

Verifies:
- HOD Dept A accessing Dept A records -> 200 OK
- HOD Dept A accessing Dept B records -> 403 Forbidden ("outside your department")
- HOD Dept B accessing Dept B records -> 200 OK
- HOD Dept B accessing Dept A records -> 403 Forbidden ("outside your department")
- HOD without faculty profile -> 403 Forbidden
- Admin can access both departments -> 200 OK
- Faculty can access both departments -> 200 OK
- Student cannot access other students' records -> 403 Forbidden
- Nonexistent records -> 404 Not Found (staff) or 403 Forbidden (student anti-enumeration)
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
os.environ["JWT_SECRET_KEY"] = "test-hod-detail-idor-secret-key-12345"

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


class TestHodCrossDepartmentDetailSecurity(unittest.TestCase):
    """Regression test suite for HOD cross-department detail IDOR security."""

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

        # 1. Departments
        self.dept_1 = Department(id=1, name="Computer Science", code="CSE")
        self.dept_2 = Department(id=2, name="Electrical Engineering", code="ECE")
        self.db.add_all([self.dept_1, self.dept_2])

        # 2. Courses
        self.course_1 = Course(id=1, department_id=1, name="B.Tech CSE", code="BTCSE", duration_years=4, total_semesters=8, is_active=True)
        self.course_2 = Course(id=2, department_id=2, name="B.Tech ECE", code="BTECE", duration_years=4, total_semesters=8, is_active=True)
        self.db.add_all([self.course_1, self.course_2])

        # 3. Subjects
        self.subject_1 = Subject(id=101, course_id=1, name="Data Structures", code="CS101", semester=1, credits=4)
        self.subject_2 = Subject(id=201, course_id=2, name="Circuits", code="EC201", semester=1, credits=4)
        self.db.add_all([self.subject_1, self.subject_2])

        # 4. Users
        self.user_hod_1 = User(id=1, email="hod1@test.com", password_hash="hash", role=UserRole.HOD, is_active=True)
        self.user_hod_2 = User(id=2, email="hod2@test.com", password_hash="hash", role=UserRole.HOD, is_active=True)
        self.user_hod_orphan = User(id=3, email="hod_orphan@test.com", password_hash="hash", role=UserRole.HOD, is_active=True)
        self.user_faculty = User(id=4, email="faculty@test.com", password_hash="hash", role=UserRole.FACULTY, is_active=True)
        self.user_admin = User(id=5, email="admin@test.com", password_hash="hash", role=UserRole.ADMIN, is_active=True)
        self.user_student_1 = User(id=6, email="student1@test.com", password_hash="hash", role=UserRole.STUDENT, is_active=True)
        self.user_student_2 = User(id=7, email="student2@test.com", password_hash="hash", role=UserRole.STUDENT, is_active=True)
        self.db.add_all([
            self.user_hod_1,
            self.user_hod_2,
            self.user_hod_orphan,
            self.user_faculty,
            self.user_admin,
            self.user_student_1,
            self.user_student_2,
        ])
        self.db.commit()

        # 5. Faculty Profiles (HODs)
        self.faculty_hod_1 = Faculty(
            id=1,
            user_id=1,
            department_id=1,
            employee_code="HOD-CSE-001",
            first_name="HOD",
            last_name="CSE",
            designation="Head of Department",
            is_active=True,
        )
        self.faculty_hod_2 = Faculty(
            id=2,
            user_id=2,
            department_id=2,
            employee_code="HOD-ECE-001",
            first_name="HOD",
            last_name="ECE",
            designation="Head of Department",
            is_active=True,
        )
        self.faculty_general = Faculty(
            id=3,
            user_id=4,
            department_id=1,
            employee_code="FAC-001",
            first_name="General",
            last_name="Faculty",
            designation="Professor",
            is_active=True,
        )
        self.db.add_all([self.faculty_hod_1, self.faculty_hod_2, self.faculty_general])

        # 6. Students in Dept 1 and Dept 2
        self.student_1 = Student(
            id=101,
            user_id=6,
            department_id=1,
            course_id=1,
            roll_number="CSE001",
            admission_year=2023,
            current_semester=1,
            name="Alice Student (CSE)",
            email="student1@test.com",
            is_active=True,
        )
        self.student_2 = Student(
            id=201,
            user_id=7,
            department_id=2,
            course_id=2,
            roll_number="ECE001",
            admission_year=2023,
            current_semester=1,
            name="Bob Student (ECE)",
            email="student2@test.com",
            is_active=True,
        )
        self.db.add_all([self.student_1, self.student_2])

        # 7. Enrollments
        self.enrollment_1 = Enrollment(
            id=1001,
            student_id=101,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment_2 = Enrollment(
            id=2001,
            student_id=201,
            subject_id=201,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add_all([self.enrollment_1, self.enrollment_2])

        # 8. Attendance
        self.attendance_1 = Attendance(
            id=10001,
            enrollment_id=1001,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
            remarks="Present in CSE",
        )
        self.attendance_2 = Attendance(
            id=20001,
            enrollment_id=2001,
            attendance_date=date(2023, 9, 1),
            status=AttendanceStatus.PRESENT,
            remarks="Present in ECE",
        )
        self.db.add_all([self.attendance_1, self.attendance_2])

        # 9. Assessments
        self.assessment_1 = Assessment(
            id=100001,
            enrollment_id=1001,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1 CSE",
            max_marks=50,
            obtained_marks=45,
            assessment_date=date(2023, 9, 20),
            remarks="Good",
        )
        self.assessment_2 = Assessment(
            id=200001,
            enrollment_id=2001,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1 ECE",
            max_marks=50,
            obtained_marks=40,
            assessment_date=date(2023, 9, 20),
            remarks="Good",
        )
        self.db.add_all([self.assessment_1, self.assessment_2])
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
        app.dependency_overrides.clear()
        self.db.close()

    def _get(self, path: str, user: User | None = None):
        self.active_user = user

        scope = {
            "type": "http",
            "method": "GET",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [(b"content-type", b"application/json")],
        }

        status_code = [None]
        response_body = []

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        async def run_app():
            await app(scope, receive, send)

        asyncio.run(run_app())

        body_bytes = b"".join(response_body)
        try:
            data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            data = {"raw": body_bytes.decode("utf-8", errors="replace")}

        return status_code[0], data

    # =========================================================================
    # 1. STUDENT DETAIL ENDPOINT TESTS
    # =========================================================================

    def test_hod_dept1_accesses_dept1_student_allowed(self):
        """HOD Dept 1 accessing Student Dept 1 -> 200 OK."""
        code, data = self._get("/api/v1/students/101", user=self.user_hod_1)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 101)
        self.assertEqual(data["department_id"], 1)

    def test_hod_dept1_accesses_dept2_student_forbidden(self):
        """HOD Dept 1 accessing Student Dept 2 -> 403 Forbidden with department scope message."""
        code, data = self._get("/api/v1/students/201", user=self.user_hod_1)
        self.assertEqual(code, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_hod_dept2_accesses_dept2_student_allowed(self):
        """HOD Dept 2 accessing Student Dept 2 -> 200 OK."""
        code, data = self._get("/api/v1/students/201", user=self.user_hod_2)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 201)
        self.assertEqual(data["department_id"], 2)

    def test_hod_dept2_accesses_dept1_student_forbidden(self):
        """HOD Dept 2 accessing Student Dept 1 -> 403 Forbidden with department scope message."""
        code, data = self._get("/api/v1/students/101", user=self.user_hod_2)
        self.assertEqual(code, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_hod_orphan_accesses_student_forbidden(self):
        """HOD without faculty profile -> 403 Forbidden."""
        code, data = self._get("/api/v1/students/101", user=self.user_hod_orphan)
        self.assertEqual(code, 403)

    def test_admin_accesses_students_across_departments(self):
        """Admin accesses Dept 1 and Dept 2 students -> 200 OK."""
        code1, data1 = self._get("/api/v1/students/101", user=self.user_admin)
        self.assertEqual(code1, 200)
        code2, data2 = self._get("/api/v1/students/201", user=self.user_admin)
        self.assertEqual(code2, 200)

    def test_faculty_accesses_students_across_departments(self):
        """Faculty accesses Dept 1 and Dept 2 students -> 200 OK."""
        code1, data1 = self._get("/api/v1/students/101", user=self.user_faculty)
        self.assertEqual(code1, 200)
        code2, data2 = self._get("/api/v1/students/201", user=self.user_faculty)
        self.assertEqual(code2, 200)

    def test_student_cannot_access_other_student_profile(self):
        """Student 1 cannot access Student 2 profile -> 403 Forbidden."""
        code, data = self._get("/api/v1/students/201", user=self.user_student_1)
        self.assertEqual(code, 403)

    def test_hod_nonexistent_student_returns_404(self):
        """HOD accessing nonexistent student ID -> 404 Not Found."""
        code, data = self._get("/api/v1/students/99999", user=self.user_hod_1)
        self.assertEqual(code, 404)

    # =========================================================================
    # 2. ENROLLMENT DETAIL ENDPOINT TESTS
    # =========================================================================

    def test_hod_dept1_accesses_dept1_enrollment_allowed(self):
        """HOD Dept 1 accessing Enrollment Dept 1 -> 200 OK."""
        code, data = self._get("/api/v1/enrollments/1001", user=self.user_hod_1)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 1001)

    def test_hod_dept1_accesses_dept2_enrollment_forbidden(self):
        """HOD Dept 1 accessing Enrollment Dept 2 -> 403 Forbidden with department scope message."""
        code, data = self._get("/api/v1/enrollments/2001", user=self.user_hod_1)
        self.assertEqual(code, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_hod_dept2_accesses_dept2_enrollment_allowed(self):
        """HOD Dept 2 accessing Enrollment Dept 2 -> 200 OK."""
        code, data = self._get("/api/v1/enrollments/2001", user=self.user_hod_2)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 2001)

    def test_hod_dept2_accesses_dept1_enrollment_forbidden(self):
        """HOD Dept 2 accessing Enrollment Dept 1 -> 403 Forbidden with department scope message."""
        code, data = self._get("/api/v1/enrollments/1001", user=self.user_hod_2)
        self.assertEqual(code, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_hod_orphan_accesses_enrollment_forbidden(self):
        """HOD without faculty profile -> 403 Forbidden."""
        code, data = self._get("/api/v1/enrollments/1001", user=self.user_hod_orphan)
        self.assertEqual(code, 403)

    def test_admin_accesses_enrollments_across_departments(self):
        """Admin accesses Dept 1 and Dept 2 enrollments -> 200 OK."""
        code1, data1 = self._get("/api/v1/enrollments/1001", user=self.user_admin)
        self.assertEqual(code1, 200)
        code2, data2 = self._get("/api/v1/enrollments/2001", user=self.user_admin)
        self.assertEqual(code2, 200)

    def test_faculty_accesses_enrollments_across_departments(self):
        """Faculty accesses Dept 1 and Dept 2 enrollments -> 200 OK."""
        code1, data1 = self._get("/api/v1/enrollments/1001", user=self.user_faculty)
        self.assertEqual(code1, 200)
        code2, data2 = self._get("/api/v1/enrollments/2001", user=self.user_faculty)
        self.assertEqual(code2, 200)

    def test_student_cannot_access_other_student_enrollment(self):
        """Student 1 cannot access Student 2 enrollment -> 403 Forbidden."""
        code, data = self._get("/api/v1/enrollments/2001", user=self.user_student_1)
        self.assertEqual(code, 403)

    def test_hod_nonexistent_enrollment_returns_404(self):
        """HOD accessing nonexistent enrollment ID -> 404 Not Found."""
        code, data = self._get("/api/v1/enrollments/99999", user=self.user_hod_1)
        self.assertEqual(code, 404)

    # =========================================================================
    # 3. ATTENDANCE DETAIL ENDPOINT TESTS
    # =========================================================================

    def test_hod_dept1_accesses_dept1_attendance_allowed(self):
        """HOD Dept 1 accessing Attendance Dept 1 -> 200 OK."""
        code, data = self._get("/api/v1/attendance/10001", user=self.user_hod_1)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 10001)

    def test_hod_dept1_accesses_dept2_attendance_forbidden(self):
        """HOD Dept 1 accessing Attendance Dept 2 -> 403 Forbidden with department scope message."""
        code, data = self._get("/api/v1/attendance/20001", user=self.user_hod_1)
        self.assertEqual(code, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_hod_dept2_accesses_dept2_attendance_allowed(self):
        """HOD Dept 2 accessing Attendance Dept 2 -> 200 OK."""
        code, data = self._get("/api/v1/attendance/20001", user=self.user_hod_2)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 20001)

    def test_hod_dept2_accesses_dept1_attendance_forbidden(self):
        """HOD Dept 2 accessing Attendance Dept 1 -> 403 Forbidden with department scope message."""
        code, data = self._get("/api/v1/attendance/10001", user=self.user_hod_2)
        self.assertEqual(code, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_hod_orphan_accesses_attendance_forbidden(self):
        """HOD without faculty profile -> 403 Forbidden."""
        code, data = self._get("/api/v1/attendance/10001", user=self.user_hod_orphan)
        self.assertEqual(code, 403)

    def test_admin_accesses_attendance_across_departments(self):
        """Admin accesses Dept 1 and Dept 2 attendance -> 200 OK."""
        code1, data1 = self._get("/api/v1/attendance/10001", user=self.user_admin)
        self.assertEqual(code1, 200)
        code2, data2 = self._get("/api/v1/attendance/20001", user=self.user_admin)
        self.assertEqual(code2, 200)

    def test_faculty_accesses_attendance_across_departments(self):
        """Faculty accesses Dept 1 and Dept 2 attendance -> 200 OK."""
        code1, data1 = self._get("/api/v1/attendance/10001", user=self.user_faculty)
        self.assertEqual(code1, 200)
        code2, data2 = self._get("/api/v1/attendance/20001", user=self.user_faculty)
        self.assertEqual(code2, 200)

    def test_student_cannot_access_other_student_attendance(self):
        """Student 1 cannot access Student 2 attendance -> 403 Forbidden."""
        code, data = self._get("/api/v1/attendance/20001", user=self.user_student_1)
        self.assertEqual(code, 403)

    def test_hod_nonexistent_attendance_returns_404(self):
        """HOD accessing nonexistent attendance ID -> 404 Not Found."""
        code, data = self._get("/api/v1/attendance/99999", user=self.user_hod_1)
        self.assertEqual(code, 404)

    # =========================================================================
    # 4. ASSESSMENT DETAIL ENDPOINT TESTS
    # =========================================================================

    def test_hod_dept1_accesses_dept1_assessment_allowed(self):
        """HOD Dept 1 accessing Assessment Dept 1 -> 200 OK."""
        code, data = self._get("/api/v1/assessments/100001", user=self.user_hod_1)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 100001)

    def test_hod_dept1_accesses_dept2_assessment_forbidden(self):
        """HOD Dept 1 accessing Assessment Dept 2 -> 403 Forbidden with department scope message."""
        code, data = self._get("/api/v1/assessments/200001", user=self.user_hod_1)
        self.assertEqual(code, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_hod_dept2_accesses_dept2_assessment_allowed(self):
        """HOD Dept 2 accessing Assessment Dept 2 -> 200 OK."""
        code, data = self._get("/api/v1/assessments/200001", user=self.user_hod_2)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 200001)

    def test_hod_dept2_accesses_dept1_assessment_forbidden(self):
        """HOD Dept 2 accessing Assessment Dept 1 -> 403 Forbidden with department scope message."""
        code, data = self._get("/api/v1/assessments/100001", user=self.user_hod_2)
        self.assertEqual(code, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_hod_orphan_accesses_assessment_forbidden(self):
        """HOD without faculty profile -> 403 Forbidden."""
        code, data = self._get("/api/v1/assessments/100001", user=self.user_hod_orphan)
        self.assertEqual(code, 403)

    def test_admin_accesses_assessments_across_departments(self):
        """Admin accesses Dept 1 and Dept 2 assessments -> 200 OK."""
        code1, data1 = self._get("/api/v1/assessments/100001", user=self.user_admin)
        self.assertEqual(code1, 200)
        code2, data2 = self._get("/api/v1/assessments/200001", user=self.user_admin)
        self.assertEqual(code2, 200)

    def test_faculty_accesses_assessments_across_departments(self):
        """Faculty accesses Dept 1 and Dept 2 assessments -> 200 OK."""
        code1, data1 = self._get("/api/v1/assessments/100001", user=self.user_faculty)
        self.assertEqual(code1, 200)
        code2, data2 = self._get("/api/v1/assessments/200001", user=self.user_faculty)
        self.assertEqual(code2, 200)

    def test_student_cannot_access_other_student_assessment(self):
        """Student 1 cannot access Student 2 assessment -> 403 Forbidden."""
        code, data = self._get("/api/v1/assessments/200001", user=self.user_student_1)
        self.assertEqual(code, 403)

    def test_hod_nonexistent_assessment_returns_404(self):
        """HOD accessing nonexistent assessment ID -> 404 Not Found."""
        code, data = self._get("/api/v1/assessments/99999", user=self.user_hod_1)
        self.assertEqual(code, 404)


if __name__ == "__main__":
    unittest.main()
