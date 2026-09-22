"""
Automated tests for VCIS 3.0 Academic Intervention REST API Router (backend/app/routers/interventions.py).

Validates:
1. Faculty can create intervention (POST /api/v1/interventions -> 201).
2. Unauthorized user cannot create intervention (missing/invalid token).
3. Student cannot create intervention (HTTP 403).
4. Created intervention is returned correctly with all expected schema fields.
5. Authenticated staff (Faculty, HOD, Admin) can retrieve an intervention.
6. Student can retrieve their own intervention (HTTP 200).
7. Student cannot retrieve another student's intervention by changing intervention_id (IDOR -> HTTP 403).
8. Student list endpoint returns only their own interventions.
9. Student cannot bypass ownership using ?student_id=<other_student_id>.
10. Faculty/HOD/Admin list behavior allows full visibility and filtering.
11. Filtering by semester works.
12. Filtering by status works.
13. Filtering by faculty_id works.
14. Update workflow fields works for authorized staff (PATCH -> 200).
15. Student cannot update intervention (PATCH -> 403).
16. Historical trigger_predicted_score cannot be changed via PATCH.
17. Historical trigger_academic_status cannot be changed via PATCH.
18. Nonexistent intervention returns HTTP 404.
19. Invalid intervention ID (<= 0) returns HTTP 400.
20. Existing prediction/status APIs remain completely unaffected.
"""

import asyncio
from datetime import date
import json
import os
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure app imports resolve cleanly
sys.path.insert(0, "backend")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-12345"

from app.base import Base
# Register all models
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

from app.models.user import User, UserRole
from app.models.department import Department
from app.models.course import Course
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.subject import Subject
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assessment import Assessment, AssessmentType
from app.models.intervention import Intervention, InterventionStatus, InterventionType
from app.services.academic_status_service import AcademicStatus

from app.main import app
from app.database import get_db
from app.core.dependencies import get_current_user


class TestInterventionRouter(unittest.TestCase):
    """Integration test suite for Intervention REST endpoints and IDOR protection."""

    @classmethod
    def setUpClass(cls):
        """Set up in-memory SQLite engine with StaticPool."""
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        """Dispose of in-memory database."""
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        """Reset data and configure user fixtures per test."""
        self.db = self.Session()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

        # Create basic departmental / course records
        self.dept = Department(id=1, name="Computer Science", code="CS")
        self.course = Course(id=1, department_id=1, name="Master of Computer Applications", code="MCA", duration_years=2, total_semesters=4)
        self.db.add_all([self.dept, self.course])
        self.db.commit()

        # Create user accounts
        self.user_admin = User(id=1, email="admin@test.com", password_hash="h1", role=UserRole.ADMIN, is_active=True)
        self.user_hod = User(id=2, email="hod@test.com", password_hash="h2", role=UserRole.HOD, is_active=True)
        self.user_faculty1 = User(id=3, email="fac1@test.com", password_hash="h3", role=UserRole.FACULTY, is_active=True)
        self.user_faculty2 = User(id=4, email="fac2@test.com", password_hash="h4", role=UserRole.FACULTY, is_active=True)
        self.user_student1 = User(id=5, email="stud1@test.com", password_hash="h5", role=UserRole.STUDENT, is_active=True)
        self.user_student2 = User(id=6, email="stud2@test.com", password_hash="h6", role=UserRole.STUDENT, is_active=True)
        self.db.add_all([
            self.user_admin,
            self.user_hod,
            self.user_faculty1,
            self.user_faculty2,
            self.user_student1,
            self.user_student2,
        ])
        self.db.commit()

        # Create faculty records
        self.faculty1 = Faculty(id=1, user_id=3, department_id=1, employee_code="F001", first_name="Alan", last_name="Turing", designation="Professor", is_active=True)
        self.faculty2 = Faculty(id=2, user_id=4, department_id=1, employee_code="F002", first_name="Grace", last_name="Hopper", designation="Associate Professor", is_active=True)
        self.faculty_hod = Faculty(id=3, user_id=2, department_id=1, employee_code="H001", first_name="HOD", last_name="User", designation="Professor & HOD", is_active=True)

        # Create student records
        self.student1 = Student(id=1, user_id=5, department_id=1, course_id=1, roll_number="MCA01", admission_year=2024, current_semester=1, name="Ada Lovelace", email="stud1@test.com", is_active=True)
        self.student2 = Student(id=2, user_id=6, department_id=1, course_id=1, roll_number="MCA02", admission_year=2024, current_semester=1, name="Charles Babbage", email="stud2@test.com", is_active=True)

        self.db.add_all([self.faculty1, self.faculty2, self.faculty_hod, self.student1, self.student2])
        self.db.commit()

        # Default authenticated user for requests
        self.active_user = self.user_faculty1
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.active_user

    def tearDown(self):
        """Clean up DB session and dependency overrides."""
        self.db.close()
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------
    # Pure ASGI Request Helper
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        json_data: dict | None = None,
        headers: list[tuple[bytes, bytes]] | None = None,
    ) -> tuple[int, dict]:
        body = json.dumps(json_data).encode("utf-8") if json_data is not None else b""
        if headers is None:
            headers = [
                (b"content-type", b"application/json"),
                (b"authorization", b"Bearer test-token"),
            ]

        query_string = b""
        path_only = path
        if "?" in path:
            path_only, qs = path.split("?", 1)
            query_string = qs.encode("utf-8")

        status_code = None
        response_body = []

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method.upper(),
            "path": path_only,
            "raw_path": path_only.encode("ascii"),
            "query_string": query_string,
            "headers": headers,
        }

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            nonlocal status_code, response_body
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        asyncio.run(app(scope, receive, send))
        raw_output = b"".join(response_body).decode("utf-8")
        parsed_json = json.loads(raw_output) if raw_output else {}
        return status_code, parsed_json

    def _post(self, path: str, json_data: dict | None = None, headers=None):
        return self._request("POST", path, json_data, headers)

    def _get(self, path: str, headers=None):
        return self._request("GET", path, headers=headers)

    def _patch(self, path: str, json_data: dict | None = None, headers=None):
        return self._request("PATCH", path, json_data, headers)

    # ------------------------------------------------------------------
    # Helper to insert an intervention directly into the DB
    # ------------------------------------------------------------------

    def _seed_intervention(
        self,
        student_id: int = 1,
        faculty_id: int = 1,
        semester: int = 1,
        intervention_type: InterventionType = InterventionType.EXTRA_CLASS,
        status: InterventionStatus = InterventionStatus.ASSIGNED,
        trigger_predicted_score: float = 48.5,
        trigger_academic_status: AcademicStatus = AcademicStatus.INTERVENTION,
    ) -> Intervention:
        inv = Intervention(
            student_id=student_id,
            faculty_id=faculty_id,
            semester=semester,
            intervention_type=intervention_type,
            status=status,
            trigger_predicted_score=trigger_predicted_score,
            trigger_academic_status=trigger_academic_status,
            description="Initial need.",
            action_plan="Initial plan.",
            follow_up_date=date(2024, 10, 1),
        )
        self.db.add(inv)
        self.db.commit()
        self.db.refresh(inv)
        return inv

    # ==================================================================
    # TEST CASES
    # ==================================================================

    def test_01_faculty_can_create_intervention(self):
        """Verify faculty can create an intervention returning HTTP 201."""
        self.active_user = self.user_faculty1
        payload = {
            "student_id": 1,
            "faculty_id": 1,
            "semester": 1,
            "intervention_type": "extra_class",
            "trigger_predicted_score": 45.8,
            "trigger_academic_status": "INTERVENTION",
            "description": "Needs assistance with programming.",
            "action_plan": "Three extra labs scheduled.",
            "follow_up_date": "2024-10-20",
        }
        status_code, body = self._post("/api/v1/interventions/", payload)
        self.assertEqual(status_code, 201)
        self.assertIn("id", body)
        self.assertEqual(body["student_id"], 1)
        self.assertEqual(body["faculty_id"], 1)
        self.assertEqual(body["intervention_type"], "extra_class")
        self.assertEqual(body["status"], "assigned")
        self.assertEqual(body["trigger_predicted_score"], 45.8)
        self.assertEqual(body["trigger_academic_status"], "INTERVENTION")

    def test_02_unauthorized_user_cannot_create_intervention(self):
        """Verify request without valid credentials is rejected."""
        app.dependency_overrides.pop(get_current_user, None)
        payload = {
            "student_id": 1,
            "faculty_id": 1,
            "semester": 1,
            "intervention_type": "counselling",
            "trigger_predicted_score": 42.0,
            "trigger_academic_status": "INTERVENTION",
        }
        status_code, _ = self._post("/api/v1/interventions/", payload, headers=[(b"content-type", b"application/json")])
        self.assertIn(status_code, [401, 403])

    def test_03_student_cannot_create_intervention(self):
        """Verify authenticated student role is forbidden from creating interventions."""
        self.active_user = self.user_student1
        payload = {
            "student_id": 1,
            "faculty_id": 1,
            "semester": 1,
            "intervention_type": "monitoring",
            "trigger_predicted_score": 52.0,
            "trigger_academic_status": "MONITOR",
        }
        status_code, body = self._post("/api/v1/interventions/", payload)
        self.assertEqual(status_code, 403)
        self.assertEqual(body["detail"], "You do not have permission to perform this action.")

    def test_04_created_intervention_returned_correctly(self):
        """Verify all fields match response schema upon creation."""
        self.active_user = self.user_admin
        payload = {
            "student_id": 2,
            "faculty_id": 2,
            "semester": 2,
            "intervention_type": "additional_assignment",
            "trigger_predicted_score": 55.45,
            "trigger_academic_status": "MONITOR",
            "description": "Additional practice needed.",
            "action_plan": "Submit tutorial 3.",
            "follow_up_date": "2024-11-15",
        }
        status_code, body = self._post("/api/v1/interventions/", payload)
        self.assertEqual(status_code, 201)
        expected_keys = {
            "id", "student_id", "faculty_id", "semester",
            "intervention_type", "status", "trigger_predicted_score",
            "trigger_academic_status", "description", "action_plan",
            "follow_up_date", "created_at", "updated_at",
        }
        self.assertEqual(set(body.keys()), expected_keys)
        self.assertEqual(body["student_id"], 2)
        self.assertEqual(body["status"], "assigned")

    def test_05_authenticated_staff_can_retrieve_intervention(self):
        """Verify Faculty, HOD, and Admin can view any intervention by ID."""
        inv = self._seed_intervention(student_id=1, faculty_id=1, semester=1)

        for staff_user in [self.user_faculty1, self.user_hod, self.user_admin]:
            with self.subTest(role=staff_user.role):
                self.active_user = staff_user
                status_code, body = self._get(f"/api/v1/interventions/{inv.id}")
                self.assertEqual(status_code, 200)
                self.assertEqual(body["id"], inv.id)

    def test_06_student_can_retrieve_own_intervention(self):
        """Verify student can retrieve an intervention assigned to them."""
        inv = self._seed_intervention(student_id=1, faculty_id=1)
        self.active_user = self.user_student1

        status_code, body = self._get(f"/api/v1/interventions/{inv.id}")
        self.assertEqual(status_code, 200)
        self.assertEqual(body["id"], inv.id)
        self.assertEqual(body["student_id"], 1)

    def test_07_student_cannot_retrieve_other_student_intervention_idor(self):
        """
        Verify student cannot access another student's intervention by ID (IDOR).
        Must return HTTP 403 Forbidden.
        """
        inv_for_student_2 = self._seed_intervention(student_id=2, faculty_id=1)

        # Authenticate as student 1
        self.active_user = self.user_student1
        status_code, body = self._get(f"/api/v1/interventions/{inv_for_student_2.id}")
        self.assertEqual(status_code, 403)
        self.assertEqual(body["detail"], "You do not have permission to access this intervention.")

    def test_08_student_list_endpoint_returns_only_own_interventions(self):
        """Verify GET /api/v1/interventions/ for a student returns ONLY their records."""
        self._seed_intervention(student_id=1, faculty_id=1)
        self._seed_intervention(student_id=1, faculty_id=2)
        self._seed_intervention(student_id=2, faculty_id=1)

        self.active_user = self.user_student1
        status_code, body = self._get("/api/v1/interventions/")
        self.assertEqual(status_code, 200)
        self.assertEqual(len(body), 2)
        for item in body:
            self.assertEqual(item["student_id"], 1)

    def test_09_student_cannot_bypass_ownership_via_query_param(self):
        """Verify student passing ?student_id=2 still receives only their own records."""
        self._seed_intervention(student_id=1, faculty_id=1)
        self._seed_intervention(student_id=2, faculty_id=1)

        self.active_user = self.user_student1
        status_code, body = self._get("/api/v1/interventions/?student_id=2")
        self.assertEqual(status_code, 200)
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["student_id"], 1)

    def test_10_staff_list_behavior_with_filters(self):
        """Verify Faculty/HOD/Admin can list all and filter by student_id."""
        self._seed_intervention(student_id=1, faculty_id=1)
        self._seed_intervention(student_id=2, faculty_id=1)

        self.active_user = self.user_faculty1
        status_code, body = self._get("/api/v1/interventions/")
        self.assertEqual(status_code, 200)
        self.assertEqual(len(body), 2)

        # Filter by student_id=2
        status_code, body = self._get("/api/v1/interventions/?student_id=2")
        self.assertEqual(status_code, 200)
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["student_id"], 2)

    def test_11_filter_by_semester_works(self):
        """Verify list endpoint semester filter."""
        self._seed_intervention(student_id=1, semester=1)
        self._seed_intervention(student_id=1, semester=2)

        self.active_user = self.user_admin
        status_code, body = self._get("/api/v1/interventions/?semester=2")
        self.assertEqual(status_code, 200)
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["semester"], 2)

    def test_12_filter_by_status_works(self):
        """Verify list endpoint status filter."""
        self._seed_intervention(student_id=1, status=InterventionStatus.ASSIGNED)
        self._seed_intervention(student_id=2, status=InterventionStatus.COMPLETED)

        self.active_user = self.user_hod
        status_code, body = self._get("/api/v1/interventions/?status=completed")
        self.assertEqual(status_code, 200)
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["status"], "completed")

    def test_13_filter_by_faculty_id_works(self):
        """Verify list endpoint faculty_id filter."""
        self._seed_intervention(student_id=1, faculty_id=1)
        self._seed_intervention(student_id=1, faculty_id=2)

        self.active_user = self.user_faculty1
        status_code, body = self._get("/api/v1/interventions/?faculty_id=2")
        self.assertEqual(status_code, 200)
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["faculty_id"], 2)

    def test_14_update_workflow_fields_works_for_staff(self):
        """Verify PATCH /api/v1/interventions/{id} updates mutable workflow fields."""
        inv = self._seed_intervention(student_id=1, status=InterventionStatus.ASSIGNED)

        self.active_user = self.user_faculty1
        patch_payload = {
            "status": "in_progress",
            "action_plan": "Student attended 2 remedial sessions.",
            "follow_up_date": "2024-11-01",
        }
        status_code, body = self._patch(f"/api/v1/interventions/{inv.id}", patch_payload)
        self.assertEqual(status_code, 200)
        self.assertEqual(body["status"], "in_progress")
        self.assertEqual(body["action_plan"], "Student attended 2 remedial sessions.")
        self.assertEqual(body["follow_up_date"], "2024-11-01")

    def test_15_student_cannot_update_intervention(self):
        """Verify students cannot update interventions (HTTP 403)."""
        inv = self._seed_intervention(student_id=1)

        self.active_user = self.user_student1
        status_code, body = self._patch(f"/api/v1/interventions/{inv.id}", {"status": "completed"})
        self.assertEqual(status_code, 403)
        self.assertEqual(body["detail"], "You do not have permission to perform this action.")

    def test_16_historical_trigger_score_cannot_be_changed(self):
        """Verify PATCH with attempted trigger_predicted_score has no effect on stored evidence."""
        inv = self._seed_intervention(student_id=1, trigger_predicted_score=48.5)

        self.active_user = self.user_faculty1
        # Attempt to inject new trigger evidence
        patch_payload = {
            "status": "in_progress",
            "trigger_predicted_score": 99.9,
        }
        status_code, body = self._patch(f"/api/v1/interventions/{inv.id}", patch_payload)
        self.assertEqual(status_code, 200)
        self.assertEqual(body["trigger_predicted_score"], 48.5)

    def test_17_historical_trigger_status_cannot_be_changed(self):
        """Verify PATCH with attempted trigger_academic_status has no effect on stored evidence."""
        inv = self._seed_intervention(student_id=1, trigger_academic_status=AcademicStatus.INTERVENTION)

        self.active_user = self.user_faculty1
        patch_payload = {
            "status": "completed",
            "trigger_academic_status": "NORMAL",
        }
        status_code, body = self._patch(f"/api/v1/interventions/{inv.id}", patch_payload)
        self.assertEqual(status_code, 200)
        self.assertEqual(body["trigger_academic_status"], "INTERVENTION")

    def test_18_nonexistent_intervention_returns_404(self):
        """Verify requesting or updating non-existent intervention returns HTTP 404."""
        self.active_user = self.user_admin
        status_code, body = self._get("/api/v1/interventions/9999")
        self.assertEqual(status_code, 404)
        self.assertIn("detail", body)

        status_code, body = self._patch("/api/v1/interventions/9999", {"status": "dismissed"})
        self.assertEqual(status_code, 404)

    def test_19_invalid_intervention_id_returns_400(self):
        """Verify ID <= 0 returns HTTP 400 Bad Request."""
        self.active_user = self.user_faculty1
        status_code, body = self._get("/api/v1/interventions/0")
        self.assertEqual(status_code, 400)
        self.assertEqual(body["detail"], "Invalid intervention ID.")

        status_code, body = self._patch("/api/v1/interventions/-5", {"status": "in_progress"})
        self.assertEqual(status_code, 400)
        self.assertEqual(body["detail"], "Invalid intervention ID.")

    def test_20_existing_prediction_and_status_apis_remain_unaffected(self):
        """
        Verify existing prediction pipeline POST /predictions/students/{id}
        remains completely operational and unaffected by intervention router additions.
        """
        self.active_user = self.user_admin
        # Setup student 1 academic records
        sub1 = Subject(id=101, course_id=1, name="C Programming", code="CS101", semester=1, credits=4, is_active=True)
        self.db.add(sub1)
        self.db.commit()

        enrollment = Enrollment(id=1, student_id=1, subject_id=101, academic_year="2024-25", status=EnrollmentStatus.ENROLLED)
        self.db.add(enrollment)
        self.db.commit()

        # Add attendance and assessment
        for i in range(1, 5):
            self.db.add(Attendance(id=10 + i, enrollment_id=1, attendance_date=date(2024, 9, i), status=AttendanceStatus.PRESENT))
        self.db.add(Attendance(id=15, enrollment_id=1, attendance_date=date(2024, 9, 5), status=AttendanceStatus.ABSENT))
        self.db.add(Assessment(id=101, enrollment_id=1, assessment_type=AssessmentType.ASSIGNMENT, assessment_name="Assig1", max_marks=100, obtained_marks=90, assessment_date=date(2024, 9, 10)))
        self.db.add(Assessment(id=102, enrollment_id=1, assessment_type=AssessmentType.CT1, assessment_name="CT1", max_marks=20, obtained_marks=17, assessment_date=date(2024, 9, 12)))
        self.db.commit()

        status_code, body = self._post("/predictions/students/1", {"semester": 1})
        self.assertEqual(status_code, 200)
        self.assertIn("predicted_final_semester_score", body)
        self.assertIn("academic_status", body)
        self.assertIn(body["academic_status"], ["NORMAL", "MONITOR", "INTERVENTION"])


if __name__ == "__main__":
    unittest.main()
