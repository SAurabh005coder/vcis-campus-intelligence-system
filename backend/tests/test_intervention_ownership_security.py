"""
VCIS 3.0 — Faculty Intervention Ownership Security Tests

Validates:
UPDATE:
1. Faculty A updates intervention assigned to Faculty A -> HTTP 200 OK.
2. Faculty A attempts to update intervention assigned to Faculty B -> HTTP 403 Forbidden.
3. Faculty A attempts to update nonexistent intervention -> HTTP 404 Not Found.
4. HOD can update intervention -> HTTP 200 OK.
5. Admin can update intervention -> HTTP 200 OK.
6. Student cannot update intervention -> HTTP 403 Forbidden.

CREATE:
7. Faculty A creates intervention assigned to Faculty A -> HTTP 201 Created.
8. Faculty A attempts to create intervention assigned to Faculty B -> HTTP 403 Forbidden.
9. HOD can create intervention using existing behavior -> HTTP 201 Created.
10. Admin can create intervention using existing behavior -> HTTP 201 Created.
11. Student cannot create intervention -> HTTP 403 Forbidden.

IMMUTABILITY:
12. Faculty cannot modify trigger_predicted_score via update payload.
13. Faculty cannot modify trigger_academic_status via update payload.
14. Existing trigger snapshot remains immutable after a successful workflow update.
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


class TestInterventionOwnershipSecurity(unittest.TestCase):
    """Test suite verifying faculty ownership enforcement on intervention create and update."""

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
        self.dept = Department(id=1, name="Computer Science", code="CS")
        self.course = Course(
            id=1,
            department_id=1,
            name="Master of Computer Applications",
            code="MCA",
            duration_years=2,
            total_semesters=4,
        )
        self.db.add_all([self.dept, self.course])

        # Users: Faculty A, Faculty B, HOD, Admin, Student
        self.user_faculty_a = User(
            id=1,
            email="faculty_a@test.com",
            password_hash="pw_fac_a",
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_faculty_b = User(
            id=2,
            email="faculty_b@test.com",
            password_hash="pw_fac_b",
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
        self.user_student = User(
            id=5,
            email="student@test.com",
            password_hash="pw_stud",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add_all([
            self.user_faculty_a,
            self.user_faculty_b,
            self.user_hod,
            self.user_admin,
            self.user_student,
        ])

        # Faculty Profiles
        self.faculty_a = Faculty(
            id=10,
            user_id=1,
            department_id=1,
            employee_code="FAC001",
            first_name="Alice",
            last_name="Professor",
            designation="Assistant Professor",
            is_active=True,
        )
        self.faculty_b = Faculty(
            id=20,
            user_id=2,
            department_id=1,
            employee_code="FAC002",
            first_name="Bob",
            last_name="Professor",
            designation="Associate Professor",
            is_active=True,
        )

        # Student Profile
        self.student = Student(
            id=100,
            user_id=5,
            department_id=1,
            course_id=1,
            roll_number="24MCA001",
            admission_year=2024,
            current_semester=1,
            name="Charlie Student",
            email="student@test.com",
            is_active=True,
        )
        self.faculty_hod = Faculty(
            id=30,
            user_id=3,
            department_id=1,
            employee_code="HOD001",
            first_name="Helen",
            last_name="HOD",
            designation="Head of Department",
            is_active=True,
        )
        self.db.add_all([self.faculty_a, self.faculty_b, self.faculty_hod, self.student])

        # Existing Interventions:
        # Int 1 assigned to Faculty A
        self.intervention_a = Intervention(
            id=1,
            student_id=100,
            faculty_id=10,
            semester=1,
            intervention_type=InterventionType.EXTRA_CLASS,
            status=InterventionStatus.ASSIGNED,
            trigger_predicted_score=52.5,
            trigger_academic_status=AcademicStatus.INTERVENTION,
            description="Remedial C programming classes",
            action_plan="3 weekly sessions",
            follow_up_date=date(2024, 10, 15),
        )
        # Int 2 assigned to Faculty B
        self.intervention_b = Intervention(
            id=2,
            student_id=100,
            faculty_id=20,
            semester=1,
            intervention_type=InterventionType.COUNSELLING,
            status=InterventionStatus.ASSIGNED,
            trigger_predicted_score=58.0,
            trigger_academic_status=AcademicStatus.MONITOR,
            description="Study habits counselling",
            action_plan="Bi-weekly check-in",
            follow_up_date=date(2024, 10, 20),
        )
        self.db.add_all([self.intervention_a, self.intervention_b])
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
        body: dict | None = None,
    ) -> tuple[int, dict]:
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

    # -------------------------------------------------------------------------
    # UPDATE TESTS
    # -------------------------------------------------------------------------

    def test_01_faculty_a_updates_own_intervention_success(self):
        """1. Faculty A updates intervention assigned to Faculty A -> 200 OK."""
        payload = {
            "status": "in_progress",
            "action_plan": "Alice updated action plan",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/1", user=self.user_faculty_a, body=payload)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["status"], "in_progress")
        self.assertEqual(data["action_plan"], "Alice updated action plan")

    def test_02_faculty_a_attempts_to_update_intervention_assigned_to_faculty_b_forbidden(self):
        """2. Faculty A attempts to update intervention assigned to Faculty B -> 403 Forbidden."""
        payload = {
            "status": "completed",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/2", user=self.user_faculty_a, body=payload)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_03_faculty_a_attempts_to_update_nonexistent_intervention_not_found(self):
        """3. Faculty A attempts to update nonexistent intervention -> 404 Not Found."""
        payload = {
            "status": "completed",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/99999", user=self.user_faculty_a, body=payload)
        self.assertEqual(code, 404)
        self.assertIn("detail", data)

    def test_04_hod_can_update_any_intervention(self):
        """4. HOD can update intervention -> existing successful behavior (200 OK)."""
        payload = {
            "status": "in_progress",
            "description": "HOD review note added",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/1", user=self.user_hod, body=payload)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["description"], "HOD review note added")

    def test_05_admin_can_update_any_intervention(self):
        """5. Admin can update intervention -> existing successful behavior (200 OK)."""
        payload = {
            "status": "completed",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/2", user=self.user_admin, body=payload)
        self.assertEqual(code, 200)
        self.assertEqual(data["id"], 2)
        self.assertEqual(data["status"], "completed")

    def test_06_student_cannot_update_intervention(self):
        """6. Student cannot update intervention -> 403 Forbidden."""
        payload = {
            "status": "dismissed",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/1", user=self.user_student, body=payload)
        self.assertEqual(code, 403)

    # -------------------------------------------------------------------------
    # CREATE TESTS
    # -------------------------------------------------------------------------

    def test_07_faculty_a_creates_intervention_assigned_to_self_success(self):
        """7. Faculty A creates intervention assigned to Faculty A -> 201 Created."""
        payload = {
            "student_id": 100,
            "faculty_id": 10,
            "semester": 1,
            "intervention_type": "additional_assignment",
            "trigger_predicted_score": 48.0,
            "trigger_academic_status": "INTERVENTION",
            "action_plan": "Practice problems",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_faculty_a, body=payload)
        self.assertEqual(code, 201)
        self.assertEqual(data["faculty_id"], 10)
        self.assertEqual(data["student_id"], 100)

    def test_08_faculty_a_attempts_to_create_intervention_assigned_to_faculty_b_forbidden(self):
        """8. Faculty A attempts to create intervention assigned to Faculty B -> 403 Forbidden."""
        payload = {
            "student_id": 100,
            "faculty_id": 20,
            "semester": 1,
            "intervention_type": "monitoring",
            "trigger_predicted_score": 48.0,
            "trigger_academic_status": "INTERVENTION",
            "action_plan": "Impersonated assignment",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_faculty_a, body=payload)
        self.assertEqual(code, 403)
        self.assertIn("detail", data)

    def test_09_hod_can_create_intervention_for_any_faculty(self):
        """9. HOD can create intervention using existing behavior -> 201 Created."""
        payload = {
            "student_id": 100,
            "faculty_id": 10,
            "semester": 1,
            "intervention_type": "counselling",
            "trigger_predicted_score": 55.0,
            "trigger_academic_status": "MONITOR",
            "action_plan": "HOD directive counselling",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_hod, body=payload)
        self.assertEqual(code, 201)
        self.assertEqual(data["faculty_id"], 10)

    def test_10_admin_can_create_intervention_for_any_faculty(self):
        """10. Admin can create intervention using existing behavior -> 201 Created."""
        payload = {
            "student_id": 100,
            "faculty_id": 20,
            "semester": 1,
            "intervention_type": "extra_class",
            "trigger_predicted_score": 50.0,
            "trigger_academic_status": "INTERVENTION",
            "action_plan": "Admin assigned class",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_admin, body=payload)
        self.assertEqual(code, 201)
        self.assertEqual(data["faculty_id"], 20)

    def test_11_student_cannot_create_intervention(self):
        """11. Student cannot create intervention -> 403 Forbidden."""
        payload = {
            "student_id": 100,
            "faculty_id": 10,
            "semester": 1,
            "intervention_type": "monitoring",
            "trigger_predicted_score": 60.0,
            "trigger_academic_status": "NORMAL",
            "action_plan": "Self intervention",
        }
        code, data = self._request("POST", "/api/v1/interventions/", user=self.user_student, body=payload)
        self.assertEqual(code, 403)

    # -------------------------------------------------------------------------
    # IMMUTABILITY TESTS
    # -------------------------------------------------------------------------

    def test_12_trigger_score_and_status_immutable_on_update(self):
        """12-14. Trigger score & status cannot be modified and remain unchanged after update."""
        payload = {
            "status": "completed",
            "trigger_predicted_score": 99.9,
            "trigger_academic_status": "NORMAL",
        }
        code, data = self._request("PATCH", "/api/v1/interventions/1", user=self.user_faculty_a, body=payload)
        self.assertEqual(code, 200)
        self.assertEqual(data["status"], "completed")
        # Trigger fields MUST remain the original snapshot values (52.5 and INTERVENTION)
        self.assertEqual(data["trigger_predicted_score"], 52.5)
        self.assertEqual(data["trigger_academic_status"], "INTERVENTION")

        # Verify directly in database
        self.db.expire_all()
        refreshed = self.db.query(Intervention).filter(Intervention.id == 1).first()
        self.assertEqual(refreshed.trigger_predicted_score, 52.5)
        self.assertEqual(refreshed.trigger_academic_status, AcademicStatus.INTERVENTION)


if __name__ == "__main__":
    unittest.main()
