"""
VCIS 3.0 — Prediction Endpoint HOD Department Scope Security Tests

Validates:
1. HOD can request prediction for a student in their own department.
2. HOD receives 403 for a student in another department.
3. HOD cannot use an arbitrary student_id to access another department.
4. HOD without Faculty profile receives 403 Forbidden.
5. HOD with Faculty profile but department_id=None receives 403 Forbidden.
6. HOD own-department prediction returns normal prediction response.
7. Prediction feature keys remain exactly the existing ML feature keys.
8. HOD cross-department request does NOT invoke feature extraction.
9. HOD cross-department request does NOT invoke prediction service.
10. HOD cross-department request does NOT invoke academic status service.
11. ADMIN retains prediction access across departments.
12. FACULTY retains prediction access across departments.
13. STUDENT retains own-student-only prediction behavior.
14. STUDENT cannot request another student's prediction.
15. Unauthenticated request remains 401 Unauthorized.
16. Existing prediction response fields remain unchanged.
17. Existing model metadata remains unchanged.
18. Existing semester 1 prediction behavior remains unchanged.
19. Existing semester 2-4 prediction behavior remains unchanged.
20. Existing CT2/final-score leakage protections remain intact.
21. Existing prediction status behavior remains intact.
22. Nonexistent student handling remains consistent (HTTP 404).
"""

import asyncio
from datetime import date
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-prediction-hod-scope-secret-key-12345"

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


class TestPredictionHodScope(unittest.TestCase):
    """Test suite verifying HOD department scoping for POST /api/v1/predictions/students/{student_id}."""

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
        self.dept_a = Department(id=1, name="Computer Applications", code="MCA")
        self.dept_b = Department(id=2, name="Mechanical Engineering", code="ME")
        self.db.add_all([self.dept_a, self.dept_b])

        # -------------------------------------------------------------
        # 2. Courses
        # -------------------------------------------------------------
        self.course_a = Course(
            id=1,
            department_id=1,
            name="MCA Course",
            code="MCA-C",
            duration_years=2,
            total_semesters=4,
        )
        self.course_b = Course(
            id=2,
            department_id=2,
            name="ME Course",
            code="ME-C",
            duration_years=2,
            total_semesters=4,
        )
        self.db.add_all([self.course_a, self.course_b])

        # -------------------------------------------------------------
        # 3. Subjects (Sem 1 & Sem 2 for both departments)
        # -------------------------------------------------------------
        self.subject_a_sem1 = Subject(
            id=101,
            course_id=1,
            name="Data Structures",
            code="MCA101",
            semester=1,
            credits=4,
        )
        self.subject_a_sem2 = Subject(
            id=102,
            course_id=1,
            name="Algorithms",
            code="MCA201",
            semester=2,
            credits=4,
        )
        self.subject_b_sem1 = Subject(
            id=201,
            course_id=2,
            name="Thermodynamics",
            code="ME101",
            semester=1,
            credits=4,
        )
        self.db.add_all([self.subject_a_sem1, self.subject_a_sem2, self.subject_b_sem1])

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
        self.db.commit()

        # -------------------------------------------------------------
        # 5. Faculty Profiles
        # -------------------------------------------------------------
        self.faculty_hod_a = Faculty(
            id=1,
            user_id=10,
            department_id=1,
            employee_code="HOD-MCA-001",
            first_name="Dr. MCA",
            last_name="HOD",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_hod_b = Faculty(
            id=2,
            user_id=11,
            department_id=2,
            employee_code="HOD-ME-001",
            first_name="Dr. ME",
            last_name="HOD",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_regular = Faculty(
            id=4,
            user_id=14,
            department_id=1,
            employee_code="FAC-001",
            first_name="Prof.",
            last_name="Faculty",
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
        self.student_b = Student(
            id=20,
            user_id=2,
            department_id=2,
            course_id=2,
            roll_number="23ME001",
            admission_year=2023,
            current_semester=1,
            name="Bob Student",
            email="student_b@test.com",
            is_active=True,
        )
        self.db.add_all([self.student_a, self.student_b])

        # -------------------------------------------------------------
        # 7. Enrollments
        # -------------------------------------------------------------
        self.enrollment_a_sem1 = Enrollment(
            id=501,
            student_id=10,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment_a_sem2 = Enrollment(
            id=502,
            student_id=10,
            subject_id=102,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.enrollment_b_sem1 = Enrollment(
            id=601,
            student_id=20,
            subject_id=201,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add_all([self.enrollment_a_sem1, self.enrollment_a_sem2, self.enrollment_b_sem1])

        # -------------------------------------------------------------
        # 8. Assessments (CT1, Assignments, Final)
        # -------------------------------------------------------------
        # Student A Sem 1
        self.ass_a_ct1 = Assessment(
            id=701,
            enrollment_id=501,
            assessment_type=AssessmentType.CT1,
            assessment_name="Cycle Test 1",
            max_marks=50.0,
            obtained_marks=45.0,
            assessment_date=date(2023, 9, 20),
        )
        self.ass_a_assign = Assessment(
            id=702,
            enrollment_id=501,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Assignment 1",
            max_marks=20.0,
            obtained_marks=18.0,
            assessment_date=date(2023, 9, 25),
        )
        self.ass_a_final = Assessment(
            id=703,
            enrollment_id=501,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Final Exam Sem 1",
            max_marks=100.0,
            obtained_marks=85.0,
            assessment_date=date(2023, 12, 10),
        )
        # Student A Sem 2
        self.ass_a_sem2_ct1 = Assessment(
            id=704,
            enrollment_id=502,
            assessment_type=AssessmentType.CT1,
            assessment_name="Sem 2 CT1",
            max_marks=50.0,
            obtained_marks=42.0,
            assessment_date=date(2024, 2, 20),
        )
        self.ass_a_sem2_assign = Assessment(
            id=705,
            enrollment_id=502,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Sem 2 Assign 1",
            max_marks=20.0,
            obtained_marks=17.0,
            assessment_date=date(2024, 2, 25),
        )

        # Student B Sem 1
        self.ass_b_ct1 = Assessment(
            id=801,
            enrollment_id=601,
            assessment_type=AssessmentType.CT1,
            assessment_name="ME CT1",
            max_marks=50.0,
            obtained_marks=35.0,
            assessment_date=date(2023, 9, 20),
        )
        self.ass_b_assign = Assessment(
            id=802,
            enrollment_id=601,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="ME Assign 1",
            max_marks=20.0,
            obtained_marks=15.0,
            assessment_date=date(2023, 9, 25),
        )
        self.db.add_all([
            self.ass_a_ct1,
            self.ass_a_assign,
            self.ass_a_final,
            self.ass_a_sem2_ct1,
            self.ass_a_sem2_assign,
            self.ass_b_ct1,
            self.ass_b_assign,
        ])

        # -------------------------------------------------------------
        # 9. Attendance
        # -------------------------------------------------------------
        for d in range(1, 11):
            self.db.add(Attendance(
                enrollment_id=501,
                attendance_date=date(2023, 9, d),
                status=AttendanceStatus.PRESENT if d <= 9 else AttendanceStatus.ABSENT,
            ))
            self.db.add(Attendance(
                enrollment_id=502,
                attendance_date=date(2024, 2, d),
                status=AttendanceStatus.PRESENT if d <= 8 else AttendanceStatus.ABSENT,
            ))
            self.db.add(Attendance(
                enrollment_id=601,
                attendance_date=date(2023, 9, d),
                status=AttendanceStatus.PRESENT if d <= 8 else AttendanceStatus.ABSENT,
            ))

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

    def _post(
        self,
        path: str,
        json_data: dict,
        user: User | None = None,
    ) -> tuple[int, dict]:
        self.active_user = user
        body = json.dumps(json_data).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
        ]
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
            "method": "POST",
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

    def test_01_hod_can_request_prediction_for_own_department_student(self):
        """1. HOD can request prediction for a student in their own department (HTTP 200)."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)
        self.assertEqual(data["semester"], 1)
        self.assertIn("predicted_final_semester_score", data)

    def test_02_hod_receives_403_for_student_in_another_department(self):
        """2. HOD receives 403 for a student in another department."""
        status, data = self._post(
            f"/predictions/students/{self.student_b.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_03_hod_cannot_use_arbitrary_student_id_to_access_another_department(self):
        """3. HOD cannot use an arbitrary student_id to access another department."""
        # HOD B attempts to predict Student A
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_b,
        )
        self.assertEqual(status, 403)
        self.assertIn("outside your department", data.get("detail", "").lower())

    def test_04_hod_without_faculty_profile_receives_403(self):
        """4. HOD without Faculty profile receives 403 Forbidden."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_unassigned,
        )
        self.assertEqual(status, 403)
        self.assertIn("faculty profile", data.get("detail", "").lower())

    def test_05_hod_with_faculty_profile_null_department_receives_403(self):
        """5. HOD with Faculty profile but department_id=None receives 403 Forbidden."""
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

    def test_06_hod_own_department_prediction_returns_normal_response(self):
        """6. HOD own-department prediction still returns the normal prediction response."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        expected_fields = {
            "student_id",
            "semester",
            "predicted_final_semester_score",
            "academic_status",
            "model_version",
            "model_type",
            "scenario",
            "features",
        }
        self.assertTrue(expected_fields.issubset(set(data.keys())))

    def test_07_prediction_feature_keys_match_ml_contract(self):
        """7. Prediction feature keys remain exactly the existing ML feature keys."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        expected_sem1_features = {
            "current_attendance",
            "current_assignment_average",
            "current_ct1_average",
        }
        self.assertEqual(set(data["features"].keys()), expected_sem1_features)

    def test_08_cross_department_request_does_not_invoke_feature_extraction(self):
        """8. Regression Test: Unauthorized HOD request does NOT invoke feature extraction."""
        with patch("app.routers.predictions.extract_ml_features") as mock_extract:
            status, data = self._post(
                f"/predictions/students/{self.student_b.id}",
                {"semester": 1},
                user=self.user_hod_a,
            )
            self.assertEqual(status, 403)
            mock_extract.assert_not_called()

    def test_09_cross_department_request_does_not_invoke_prediction_service(self):
        """9. Regression Test: Unauthorized HOD request does NOT invoke prediction service."""
        with patch("app.routers.predictions.predict_final_score") as mock_predict:
            status, data = self._post(
                f"/predictions/students/{self.student_b.id}",
                {"semester": 1},
                user=self.user_hod_a,
            )
            self.assertEqual(status, 403)
            mock_predict.assert_not_called()

    def test_10_cross_department_request_does_not_invoke_academic_status_service(self):
        """10. Regression Test: Unauthorized HOD request does NOT invoke academic status service."""
        with patch("app.routers.predictions.get_academic_status") as mock_status:
            status, data = self._post(
                f"/predictions/students/{self.student_b.id}",
                {"semester": 1},
                user=self.user_hod_a,
            )
            self.assertEqual(status, 403)
            mock_status.assert_not_called()

    def test_11_admin_retains_prediction_access_across_departments(self):
        """11. ADMIN retains prediction access across departments (HTTP 200)."""
        # Admin predicts Student A
        status_a, _ = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_admin,
        )
        self.assertEqual(status_a, 200)

        # Admin predicts Student B
        status_b, _ = self._post(
            f"/predictions/students/{self.student_b.id}",
            {"semester": 1},
            user=self.user_admin,
        )
        self.assertEqual(status_b, 200)

    def test_12_faculty_retains_prediction_access_across_departments(self):
        """12. FACULTY retains prediction access across departments (HTTP 200)."""
        # Faculty predicts Student A
        status_a, _ = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_faculty,
        )
        self.assertEqual(status_a, 200)

        # Faculty predicts Student B
        status_b, _ = self._post(
            f"/predictions/students/{self.student_b.id}",
            {"semester": 1},
            user=self.user_faculty,
        )
        self.assertEqual(status_b, 200)

    def test_13_student_retains_own_student_only_prediction_behavior(self):
        """13. STUDENT retains own-student-only prediction behavior (HTTP 200)."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["student_id"], self.student_a.id)

    def test_14_student_cannot_request_another_students_prediction(self):
        """14. STUDENT cannot request another student's prediction (HTTP 403 Forbidden)."""
        status, data = self._post(
            f"/predictions/students/{self.student_b.id}",
            {"semester": 1},
            user=self.user_student_a,
        )
        self.assertEqual(status, 403)
        self.assertIn("permission", data.get("detail", "").lower())

    def test_15_unauthenticated_request_remains_401(self):
        """15. Unauthenticated request remains 401 Unauthorized."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=None,
        )
        self.assertEqual(status, 401)

    def test_16_existing_prediction_response_fields_remain_unchanged(self):
        """16. Existing prediction response fields remain unchanged."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(data["predicted_final_semester_score"], float)
        self.assertIsInstance(data["academic_status"], str)
        self.assertIn("features", data)

    def test_17_existing_model_metadata_remains_unchanged(self):
        """17. Existing model metadata remains unchanged."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["model_version"], "1.0")
        self.assertEqual(data["scenario"], "Semester 1")

    def test_18_existing_semester_1_prediction_behavior_remains_unchanged(self):
        """18. Existing semester 1 prediction behavior remains unchanged."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["semester"], 1)
        self.assertIn("current_attendance", data["features"])
        self.assertNotIn("previous_semester_score", data["features"])

    def test_19_existing_semester_2_4_prediction_behavior_remains_unchanged(self):
        """19. Existing semester 2-4 prediction behavior remains unchanged."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 2},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["semester"], 2)
        self.assertIn("previous_semester_score", data["features"])
        self.assertIn("previous_semester_attendance", data["features"])

    def test_20_existing_ct2_final_score_leakage_protections_remain_intact(self):
        """20. Existing CT2/final-score leakage protections remain intact in features."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        features = data["features"]
        self.assertNotIn("current_ct2_average", features)
        self.assertNotIn("ct2", features)
        self.assertNotIn("final_score", features)
        self.assertNotIn("student_id", features)

    def test_21_existing_prediction_status_behavior_remains_intact(self):
        """21. Existing prediction status behavior remains intact."""
        status, data = self._post(
            f"/predictions/students/{self.student_a.id}",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 200)
        academic_status = data["academic_status"]
        self.assertIn(academic_status, ["NORMAL", "MONITOR", "INTERVENTION"])

    def test_22_nonexistent_student_behavior_remains_consistent(self):
        """22. Nonexistent student handling returns HTTP 404 for authorized HOD."""
        status, data = self._post(
            "/predictions/students/99999",
            {"semester": 1},
            user=self.user_hod_a,
        )
        self.assertEqual(status, 404)
        self.assertIn("not found", data.get("detail", "").lower())


if __name__ == "__main__":
    unittest.main()
