"""
VCIS 3.0 — HOD Department Scope Security Tests for Interventions

Tests:
1. HOD can list interventions for own department.
2. HOD list excludes interventions from other departments.
3. HOD list with explicit student_id cannot bypass department scope.
4. HOD list with explicit faculty_id cannot bypass department scope.
5. HOD list with semester/status filters preserves department scope.
6. HOD can retrieve own-department intervention.
7. HOD cannot retrieve another-department intervention -> 403.
8. HOD cannot retrieve nonexistent intervention if existing semantics require 404.
9. HOD can create intervention for own-department student.
10. HOD cannot create intervention for another-department student -> 403.
11. HOD cannot create intervention for nonexistent student -> preserve 404 behavior.
12. HOD can update own-department intervention.
13. HOD cannot update another-department intervention -> 403.
14. HOD without Faculty profile -> 403.
15. HOD with null department_id -> 403.
16. Faculty ownership rules still pass.
17. Student own-intervention visibility still passes.
18. Student cannot access another student's intervention.
19. Admin remains globally authorized.
20. Existing trigger_predicted_score and trigger_academic_status remain immutable.
21. No automatic intervention creation occurs from prediction.
22. Unauthenticated access remains 401.
23. Scope is based on Student.department_id: Student A in Dept 1, Faculty B in Dept 2 -> HOD A allowed.
24. Scope is NOT based on Faculty.department_id: Student B in Dept 2, Faculty A in Dept 1 -> HOD A gets 403.
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
os.environ["JWT_SECRET_KEY"] = "test-security-intervention-secret-key-12345"

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
import app.models.intervention

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.models.course import Course
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.intervention import Intervention, InterventionStatus, InterventionType
from app.models.student import Student
from app.models.user import User, UserRole
from app.services.academic_status_service import AcademicStatus


class TestInterventionHodScope(unittest.TestCase):
    """Test suite verifying HOD department scoping across all Intervention endpoints."""

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
        # 1. Departments & Courses
        # -------------------------------------------------------------
        self.dept_a = Department(id=1, name="Department A (CS)", code="CS")
        self.dept_b = Department(id=2, name="Department B (EE)", code="EE")
        self.course_a = Course(
            id=1,
            department_id=1,
            name="Master of Computer Applications",
            code="MCA",
            duration_years=2,
            total_semesters=4,
        )
        self.course_b = Course(
            id=2,
            department_id=2,
            name="Master of Electrical Engineering",
            code="MEE",
            duration_years=2,
            total_semesters=4,
        )
        self.db.add_all([self.dept_a, self.dept_b, self.course_a, self.course_b])

        # -------------------------------------------------------------
        # 2. Users
        # -------------------------------------------------------------
        # HOD A (Dept A)
        self.user_hod_a = User(
            id=1,
            email="hod_a@test.com",
            password_hash="hashed_pw",
            role=UserRole.HOD,
            is_active=True,
        )
        # HOD B (Dept B)
        self.user_hod_b = User(
            id=2,
            email="hod_b@test.com",
            password_hash="hashed_pw",
            role=UserRole.HOD,
            is_active=True,
        )
        # HOD without Faculty Profile
        self.user_hod_no_fac = User(
            id=3,
            email="hod_nofac@test.com",
            password_hash="hashed_pw",
            role=UserRole.HOD,
            is_active=True,
        )
        # Faculty A (Dept A)
        self.user_faculty_a = User(
            id=5,
            email="faculty_a@test.com",
            password_hash="hashed_pw",
            role=UserRole.FACULTY,
            is_active=True,
        )
        # Faculty B (Dept B)
        self.user_faculty_b = User(
            id=6,
            email="faculty_b@test.com",
            password_hash="hashed_pw",
            role=UserRole.FACULTY,
            is_active=True,
        )
        # Admin
        self.user_admin = User(
            id=7,
            email="admin@test.com",
            password_hash="hashed_pw",
            role=UserRole.ADMIN,
            is_active=True,
        )
        # Student A (Dept A)
        self.user_student_a = User(
            id=8,
            email="student_a@test.com",
            password_hash="hashed_pw",
            role=UserRole.STUDENT,
            is_active=True,
        )
        # Student B (Dept B)
        self.user_student_b = User(
            id=9,
            email="student_b@test.com",
            password_hash="hashed_pw",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add_all([
            self.user_hod_a,
            self.user_hod_b,
            self.user_hod_no_fac,
            self.user_faculty_a,
            self.user_faculty_b,
            self.user_admin,
            self.user_student_a,
            self.user_student_b,
        ])

        # -------------------------------------------------------------
        # 3. Faculty Profiles
        # -------------------------------------------------------------
        self.faculty_hod_a = Faculty(
            id=10,
            user_id=1,
            department_id=1,
            employee_code="HODA01",
            first_name="Dr. Alice",
            last_name="HOD",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_hod_b = Faculty(
            id=11,
            user_id=2,
            department_id=2,
            employee_code="HODB01",
            first_name="Dr. Bob",
            last_name="HOD",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_a = Faculty(
            id=13,
            user_id=5,
            department_id=1,
            employee_code="FACA01",
            first_name="Prof. Frank",
            last_name="DeptA",
            designation="Assistant Professor",
            is_active=True,
        )
        self.faculty_b = Faculty(
            id=14,
            user_id=6,
            department_id=2,
            employee_code="FACB01",
            first_name="Prof. Gary",
            last_name="DeptB",
            designation="Associate Professor",
            is_active=True,
        )
        self.db.add_all([
            self.faculty_hod_a,
            self.faculty_hod_b,
            self.faculty_a,
            self.faculty_b,
        ])

        # -------------------------------------------------------------
        # 4. Student Profiles
        # -------------------------------------------------------------
        self.student_a = Student(
            id=101,
            user_id=8,
            department_id=1,
            course_id=1,
            roll_number="24MCA001",
            admission_year=2024,
            current_semester=1,
            name="Alice Student",
            email="student_a@test.com",
            is_active=True,
        )
        self.student_b = Student(
            id=102,
            user_id=9,
            department_id=2,
            course_id=2,
            roll_number="24MEE001",
            admission_year=2024,
            current_semester=1,
            name="Bob Student",
            email="student_b@test.com",
            is_active=True,
        )
        self.db.add_all([self.student_a, self.student_b])

        # -------------------------------------------------------------
        # 5. Interventions
        # -------------------------------------------------------------
        # Intervention 1: Student A (Dept 1), Faculty A (Dept 1)
        self.int_a = Intervention(
            id=1,
            student_id=101,
            faculty_id=13,
            semester=1,
            intervention_type=InterventionType.EXTRA_CLASS,
            status=InterventionStatus.ASSIGNED,
            trigger_predicted_score=48.5,
            trigger_academic_status=AcademicStatus.INTERVENTION,
            description="Remedial programming in C",
            action_plan="3 weekly sessions",
            follow_up_date=date(2024, 10, 15),
        )
        # Intervention 2: Student B (Dept 2), Faculty B (Dept 2)
        self.int_b = Intervention(
            id=2,
            student_id=102,
            faculty_id=14,
            semester=1,
            intervention_type=InterventionType.COUNSELLING,
            status=InterventionStatus.ASSIGNED,
            trigger_predicted_score=52.0,
            trigger_academic_status=AcademicStatus.MONITOR,
            description="Circuits study counselling",
            action_plan="Bi-weekly review",
            follow_up_date=date(2024, 10, 20),
        )
        # Intervention 3: Student A (Dept 1), Faculty B (Dept 2)
        # Cross-department faculty: Student is in Dept 1!
        self.int_cross_student_a_fac_b = Intervention(
            id=3,
            student_id=101,
            faculty_id=14,
            semester=2,
            intervention_type=InterventionType.MONITORING,
            status=InterventionStatus.IN_PROGRESS,
            trigger_predicted_score=54.0,
            trigger_academic_status=AcademicStatus.MONITOR,
            description="Cross-dept electronics monitoring",
            action_plan="Weekly check-in",
            follow_up_date=date(2024, 11, 1),
        )
        # Intervention 4: Student B (Dept 2), Faculty A (Dept 1)
        # Cross-department faculty: Student is in Dept 2!
        self.int_cross_student_b_fac_a = Intervention(
            id=4,
            student_id=102,
            faculty_id=13,
            semester=2,
            intervention_type=InterventionType.ADDITIONAL_ASSIGNMENT,
            status=InterventionStatus.COMPLETED,
            trigger_predicted_score=45.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
            description="Cross-dept programming assignment",
            action_plan="Submit 5 assignments",
            follow_up_date=date(2024, 11, 10),
        )
        self.db.add_all([
            self.int_a,
            self.int_b,
            self.int_cross_student_a_fac_b,
            self.int_cross_student_b_fac_a,
        ])
        self.db.commit()

        # Dependency Overrides
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
        body: dict | None = None,
    ) -> tuple[int, dict | list]:
        self.active_user = user
        headers = [(b"content-type", b"application/json")]
        if user is not None:
            headers.append((b"authorization", b"Bearer mock-token"))

        response_body = []
        status_code = [0]
        body_bytes = json.dumps(body).encode("utf-8") if body is not None else b""

        async def send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        raw_path = path.split("?")[0].encode("ascii")
        query_string = path.split("?")[1].encode("ascii") if "?" in path else b""

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "path": path.split("?")[0],
            "raw_path": raw_path,
            "query_string": query_string,
            "headers": headers,
        }

        async def run_app():
            await app(scope, receive, send)

        asyncio.run(run_app())

        res_bytes = b"".join(response_body)
        try:
            data = json.loads(res_bytes.decode("utf-8")) if res_bytes else {}
        except Exception:
            data = {"raw": res_bytes.decode("utf-8", errors="replace")}

        return status_code[0], data

    # =========================================================================
    # 1. LIST ENDPOINT TESTS
    # =========================================================================

    def test_01_hod_can_list_interventions_for_own_department(self):
        """1. HOD can list interventions for own department."""
        code, data = self._request("GET", "/api/v1/interventions/", user=self.user_hod_a)
        self.assertEqual(code, 200)
        self.assertIsInstance(data, list)
        returned_ids = {item["id"] for item in data}
        # Interventions 1 and 3 belong to Student A (Dept 1)
        self.assertIn(1, returned_ids)
        self.assertIn(3, returned_ids)

    def test_02_hod_list_excludes_interventions_from_other_departments(self):
        """2. HOD list excludes interventions from other departments."""
        code, data = self._request("GET", "/api/v1/interventions/", user=self.user_hod_a)
        self.assertEqual(code, 200)
        returned_ids = {item["id"] for item in data}
        # Interventions 2 and 4 belong to Student B (Dept 2)
        self.assertNotIn(2, returned_ids)
        self.assertNotIn(4, returned_ids)

    def test_03_hod_list_with_explicit_student_id_cannot_bypass_scope(self):
        """3. HOD list with explicit student_id cannot bypass department scope."""
        # HOD A requests interventions with student_id=102 (Student B, Dept 2)
        code, data = self._request(
            "GET",
            f"/api/v1/interventions/?student_id={self.student_b.id}",
            user=self.user_hod_a,
        )
        self.assertEqual(code, 200)
        self.assertEqual(data, [])

    def test_04_hod_list_with_explicit_faculty_id_cannot_bypass_scope(self):
        """4. HOD list with explicit faculty_id cannot bypass department scope."""
        # Faculty B (id=14) is assigned to Int 2 (Dept 2 student) and Int 3 (Dept 1 student).
        # HOD A requests with faculty_id=14. Only Int 3 (Dept 1 student) must be returned!
        code, data = self._request(
            "GET",
            f"/api/v1/interventions/?faculty_id={self.faculty_b.id}",
            user=self.user_hod_a,
        )
        self.assertEqual(code, 200)
        self.assertIsInstance(data, list)
        returned_ids = {item["id"] for item in data}
        self.assertIn(3, returned_ids)
        self.assertNotIn(2, returned_ids)

    def test_05_hod_list_with_semester_and_status_filters_preserves_scope(self):
        """5. HOD list with semester/status filters preserves department scope."""
        # In Dept 1: Int 1 is semester 1, status assigned. Int 3 is semester 2, status in_progress.
        # In Dept 2: Int 2 is semester 1, status assigned.
        code, data = self._request(
            "GET",
            "/api/v1/interventions/?semester=1&status=assigned",
            user=self.user_hod_a,
        )
        self.assertEqual(code, 200)
        returned_ids = {item["id"] for item in data}
        self.assertIn(1, returned_ids)
        self.assertNotIn(2, returned_ids)
        self.assertNotIn(3, returned_ids)

    # =========================================================================
    # 2. GET DETAIL ENDPOINT TESTS
    # =========================================================================

    def test_06_hod_can_retrieve_own_department_intervention(self):
        """6. HOD can retrieve own-department intervention."""
        code, data = self._request("GET", "/api/v1/interventions/1", user=self.user_hod_a)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["student_id"], self.student_a.id)

    def test_07_hod_cannot_retrieve_another_department_intervention(self):
        """7. HOD cannot retrieve another-department intervention -> 403 Forbidden."""
        code, data = self._request("GET", "/api/v1/interventions/2", user=self.user_hod_a)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_08_hod_cannot_retrieve_nonexistent_intervention(self):
        """8. HOD cannot retrieve nonexistent intervention if existing semantics require 404."""
        code, data = self._request("GET", "/api/v1/interventions/99999", user=self.user_hod_a)
        self.assertEqual(code, 404)
        self.assertIn("detail", data)

    # =========================================================================
    # 3. CREATE ENDPOINT TESTS
    # =========================================================================

    def test_09_hod_can_create_intervention_for_own_department_student(self):
        """9. HOD can create intervention for own-department student."""
        payload = {
            "student_id": self.student_a.id,
            "faculty_id": self.faculty_a.id,
            "semester": 1,
            "intervention_type": "counselling",
            "trigger_predicted_score": 49.0,
            "trigger_academic_status": "INTERVENTION",
            "description": "Created by HOD A",
            "action_plan": "HOD plan",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_hod_a, body=payload)
        self.assertEqual(code, 201)
        self.assertEqual(data["student_id"], self.student_a.id)
        self.assertEqual(data["description"], "Created by HOD A")

    def test_10_hod_cannot_create_intervention_for_another_department_student(self):
        """10. HOD cannot create intervention for another-department student -> 403 Forbidden."""
        payload = {
            "student_id": self.student_b.id,
            "faculty_id": self.faculty_a.id,
            "semester": 1,
            "intervention_type": "extra_class",
            "trigger_predicted_score": 45.0,
            "trigger_academic_status": "INTERVENTION",
            "action_plan": "Cross-dept attempt",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_hod_a, body=payload)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_11_hod_cannot_create_intervention_for_nonexistent_student(self):
        """11. HOD cannot create intervention for nonexistent student -> preserve 404 behavior."""
        payload = {
            "student_id": 99999,
            "faculty_id": self.faculty_a.id,
            "semester": 1,
            "intervention_type": "extra_class",
            "trigger_predicted_score": 45.0,
            "trigger_academic_status": "INTERVENTION",
            "action_plan": "Nonexistent student attempt",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_hod_a, body=payload)
        self.assertEqual(code, 404)
        self.assertIn("detail", data)

    # =========================================================================
    # 4. UPDATE ENDPOINT TESTS
    # =========================================================================

    def test_12_hod_can_update_own_department_intervention(self):
        """12. HOD can update own-department intervention."""
        payload = {
            "status": "in_progress",
            "action_plan": "HOD A revised plan",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/1", user=self.user_hod_a, body=payload)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["status"], "in_progress")
        self.assertEqual(data["action_plan"], "HOD A revised plan")

    def test_13_hod_cannot_update_another_department_intervention(self):
        """13. HOD cannot update another-department intervention -> 403 Forbidden."""
        payload = {
            "status": "completed",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/2", user=self.user_hod_a, body=payload)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    # =========================================================================
    # 5. HOD PREREQUISITE FAILURE TESTS
    # =========================================================================

    def test_14_hod_without_faculty_profile_receives_403(self):
        """14. HOD without Faculty profile -> 403 Forbidden on all endpoints."""
        # GET list
        code, _ = self._request("GET", "/api/v1/interventions/", user=self.user_hod_no_fac)
        self.assertEqual(code, 403)
        # GET detail
        code, _ = self._request("GET", "/api/v1/interventions/1", user=self.user_hod_no_fac)
        self.assertEqual(code, 403)
        # POST
        payload = {
            "student_id": self.student_a.id,
            "faculty_id": self.faculty_a.id,
            "semester": 1,
            "intervention_type": "counselling",
            "trigger_predicted_score": 49.0,
            "trigger_academic_status": "INTERVENTION",
        }
        code, _ = self._request("POST", "/api/v1/interventions/", user=self.user_hod_no_fac, body=payload)
        self.assertEqual(code, 403)
        # PATCH
        code, _ = self._request("PATCH", "/api/v1/interventions/1", user=self.user_hod_no_fac, body={"status": "completed"})
        self.assertEqual(code, 403)

    def test_15_hod_with_null_department_id_receives_403(self):
        """15. HOD with Faculty profile but department_id=None receives 403 Forbidden."""
        from unittest.mock import MagicMock, patch
        from app.core.authorization import resolve_hod_department_id
        from fastapi import HTTPException

        # 1. Direct resolver validation with mock Faculty having department_id=None
        mock_faculty = Faculty(
            id=99,
            user_id=self.user_hod_no_fac.id,
            department_id=1,
            employee_code="HODNULL",
            first_name="Null",
            last_name="Dept",
            designation="Professor & HOD",
        )
        mock_faculty.department_id = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_faculty

        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_hod_no_fac, mock_db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("assigned department", ctx.exception.detail.lower())

        # 2. Endpoint behavior when department_id is null
        with patch("app.routers.interventions.resolve_hod_department_id") as mock_resolve:
            mock_resolve.side_effect = HTTPException(
                status_code=403,
                detail="HOD faculty profile has no assigned department.",
            )
            # GET list
            code, _ = self._request("GET", "/api/v1/interventions/", user=self.user_hod_a)
            self.assertEqual(code, 403)
            # GET detail
            code, _ = self._request("GET", "/api/v1/interventions/1", user=self.user_hod_a)
            self.assertEqual(code, 403)
            # POST
            payload = {
                "student_id": self.student_a.id,
                "faculty_id": self.faculty_a.id,
                "semester": 1,
                "intervention_type": "counselling",
                "trigger_predicted_score": 49.0,
                "trigger_academic_status": "INTERVENTION",
            }
            code, _ = self._request("POST", "/api/v1/interventions/", user=self.user_hod_a, body=payload)
            self.assertEqual(code, 403)
            # PATCH
            code, _ = self._request("PATCH", "/api/v1/interventions/1", user=self.user_hod_a, body={"status": "completed"})
            self.assertEqual(code, 403)

    # =========================================================================
    # 6. FACULTY & STUDENT REGRESSION TESTS
    # =========================================================================

    def test_16_faculty_ownership_rules_still_pass(self):
        """16. Faculty ownership rules still pass (self-assignment on create, assigned-only on update)."""
        # Faculty A creates assigned to Faculty A -> 201
        payload = {
            "student_id": self.student_a.id,
            "faculty_id": self.faculty_a.id,
            "semester": 1,
            "intervention_type": "additional_assignment",
            "trigger_predicted_score": 45.0,
            "trigger_academic_status": "INTERVENTION",
            "action_plan": "Practice",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_faculty_a, body=payload)
        self.assertEqual(code, 201)

        # Faculty A attempts to create assigned to Faculty B -> 403
        payload["faculty_id"] = self.faculty_b.id
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_faculty_a, body=payload)
        self.assertEqual(code, 403)

        # Faculty A updates Int 1 (assigned to Faculty A) -> 200
        code, data = self._request(
            "PATCH",
            "/api/v1/interventions/1",
            user=self.user_faculty_a,
            body={"status": "in_progress"},
        )
        self.assertEqual(code, 200)

        # Faculty A attempts to update Int 2 (assigned to Faculty B) -> 403
        code, data = self._request(
            "PATCH",
            "/api/v1/interventions/2",
            user=self.user_faculty_a,
            body={"status": "completed"},
        )
        self.assertEqual(code, 403)

    def test_17_student_own_intervention_visibility_still_passes(self):
        """17. Student own-intervention visibility still passes."""
        # Student A retrieves own intervention 1 -> 200
        code, data = self._request("GET", "/api/v1/interventions/1", user=self.user_student_a)
        self.assertEqual(code, 200)
        self.assertEqual(data["student_id"], self.student_a.id)

        # Student A lists interventions -> only own interventions returned
        code, data = self._request("GET", "/api/v1/interventions/", user=self.user_student_a)
        self.assertEqual(code, 200)
        returned_ids = {item["id"] for item in data}
        self.assertEqual(returned_ids, {1, 3})

    def test_18_student_cannot_access_another_students_intervention(self):
        """18. Student cannot access another student's intervention -> 403 Forbidden."""
        # Student A tries to view Student B's intervention 2 -> 403
        code, data = self._request("GET", "/api/v1/interventions/2", user=self.user_student_a)
        self.assertEqual(code, 403)

        # Student cannot create or update
        code, _ = self._request("POST", "/api/v1/interventions/", user=self.user_student_a, body={})
        self.assertEqual(code, 403)
        code, _ = self._request("PATCH", "/api/v1/interventions/1", user=self.user_student_a, body={})
        self.assertEqual(code, 403)

    def test_19_admin_remains_globally_authorized(self):
        """19. Admin remains globally authorized across all departments."""
        # Admin can view Int 1 (Dept 1) and Int 2 (Dept 2)
        code, _ = self._request("GET", "/api/v1/interventions/1", user=self.user_admin)
        self.assertEqual(code, 200)
        code, _ = self._request("GET", "/api/v1/interventions/2", user=self.user_admin)
        self.assertEqual(code, 200)

        # Admin lists all
        code, data = self._request("GET", "/api/v1/interventions/", user=self.user_admin)
        self.assertEqual(code, 200)
        returned_ids = {item["id"] for item in data}
        self.assertTrue({1, 2, 3, 4}.issubset(returned_ids))

        # Admin can create for Dept 2
        payload = {
            "student_id": self.student_b.id,
            "faculty_id": self.faculty_b.id,
            "semester": 1,
            "intervention_type": "counselling",
            "trigger_predicted_score": 55.0,
            "trigger_academic_status": "MONITOR",
        }
        code, _ = self._request("POST", "/api/v1/interventions/", user=self.user_admin, body=payload)
        self.assertEqual(code, 201)

        # Admin can update Int 2
        code, _ = self._request(
            "PATCH",
            "/api/v1/interventions/2",
            user=self.user_admin,
            body={"status": "completed"},
        )
        self.assertEqual(code, 200)

    def test_20_trigger_score_and_status_remain_immutable(self):
        """20. Existing trigger_predicted_score and trigger_academic_status remain immutable."""
        orig_score = self.int_a.trigger_predicted_score
        orig_status = self.int_a.trigger_academic_status

        # Attempt to supply trigger fields in PATCH
        payload = {
            "status": "in_progress",
            "trigger_predicted_score": 99.9,
            "trigger_academic_status": "NORMAL",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/1", user=self.user_hod_a, body=payload)
        self.assertEqual(code, 200)
        self.assertEqual(data["trigger_predicted_score"], orig_score)
        self.assertEqual(data["trigger_academic_status"], orig_status.value)

    def test_21_no_automatic_intervention_creation_occurs(self):
        """21. Interventions are created only explicitly, not automatically."""
        # Query current count
        count_before = self.db.query(Intervention).count()
        # Non-creation request
        self._request("GET", "/api/v1/interventions/", user=self.user_hod_a)
        count_after = self.db.query(Intervention).count()
        self.assertEqual(count_before, count_after)

    def test_22_unauthenticated_access_remains_401(self):
        """22. Unauthenticated access remains 401 Unauthorized."""
        code, _ = self._request("GET", "/api/v1/interventions/", user=None)
        self.assertEqual(code, 401)
        code, _ = self._request("GET", "/api/v1/interventions/1", user=None)
        self.assertEqual(code, 401)
        code, _ = self._request("POST", "/api/v1/interventions/", user=None, body={})
        self.assertEqual(code, 401)
        code, _ = self._request("PATCH", "/api/v1/interventions/1", user=None, body={})
        self.assertEqual(code, 401)

    # =========================================================================
    # 7. EXPLICIT STUDENT VS FACULTY DEPARTMENT AUTHORITY TESTS
    # =========================================================================

    def test_23_student_in_dept_a_faculty_in_dept_b_hod_a_can_access(self):
        """
        23. IMPORTANT SECURITY TEST:
        Student belongs to Dept A, Assigned Faculty belongs to Dept B.
        HOD A (Dept A) MUST be allowed because intervention scope is determined
        by the STUDENT'S department.
        """
        # GET Detail for Int 3 (Student A in Dept 1, Faculty B in Dept 2)
        code, data = self._request("GET", "/api/v1/interventions/3", user=self.user_hod_a)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 3)
        self.assertEqual(data["student_id"], self.student_a.id)

        # PATCH for Int 3
        code, data = self._request(
            "PATCH",
            "/api/v1/interventions/3",
            user=self.user_hod_a,
            body={"description": "HOD A update on cross-faculty intervention"},
        )
        self.assertEqual(code, 200)

        # POST assigning cross-dept faculty (Faculty B) to student in Dept A
        payload = {
            "student_id": self.student_a.id,
            "faculty_id": self.faculty_b.id,
            "semester": 2,
            "intervention_type": "extra_class",
            "trigger_predicted_score": 50.0,
            "trigger_academic_status": "INTERVENTION",
            "description": "Cross faculty assignment by HOD A",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_hod_a, body=payload)
        self.assertEqual(code, 201)
        self.assertEqual(data["faculty_id"], self.faculty_b.id)
        self.assertEqual(data["student_id"], self.student_a.id)

    def test_24_student_in_dept_b_faculty_in_dept_a_hod_a_cannot_access(self):
        """
        24. IMPORTANT SECURITY TEST:
        Student belongs to Dept B, Assigned Faculty belongs to Dept A.
        HOD A (Dept A) MUST NOT be allowed (403) because intervention scope is
        determined by the STUDENT'S department, not Faculty department.
        """
        # GET Detail for Int 4 (Student B in Dept 2, Faculty A in Dept 1)
        code, data = self._request("GET", "/api/v1/interventions/4", user=self.user_hod_a)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

        # PATCH for Int 4
        code, data = self._request(
            "PATCH",
            "/api/v1/interventions/4",
            user=self.user_hod_a,
            body={"status": "dismissed"},
        )
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

        # POST assigning Faculty A to Student B
        payload = {
            "student_id": self.student_b.id,
            "faculty_id": self.faculty_a.id,
            "semester": 2,
            "intervention_type": "extra_class",
            "trigger_predicted_score": 50.0,
            "trigger_academic_status": "INTERVENTION",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_hod_a, body=payload)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)


if __name__ == "__main__":
    unittest.main()
