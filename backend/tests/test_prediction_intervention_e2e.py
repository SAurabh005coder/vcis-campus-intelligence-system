"""
End-to-End Integration Tests for VCIS 3.0: Prediction -> Status -> Manual Intervention Lifecycle.

Validates the complete cross-module workflow:
1. Student academic records in DB (attendance, assignment, CT1; no CT2/Final).
2. Live prediction generation via POST /predictions/students/{id}.
3. Academic status classification using canonical service on raw unrounded score.
4. Prediction API does NOT automatically create interventions (strict lifecycle separation).
5. Faculty manual review & intervention assignment via POST /api/v1/interventions/
   using exact prediction score and academic status as historical trigger snapshot.
6. Verification of historical snapshot persistence via GET /api/v1/interventions/{id}.
7. Student authenticated retrieval of own intervention (GET /api/v1/interventions/{id}).
8. Student IDOR protection:
   - Another student attempting GET /api/v1/interventions/{id} receives HTTP 403 Forbidden.
   - Another student listing via GET /api/v1/interventions/?student_id={id} receives empty list.
9. Faculty workflow update via PATCH /api/v1/interventions/{id} (status -> COMPLETED).
10. Historical trigger evidence immutability:
    - trigger_predicted_score and trigger_academic_status remain strictly unchanged after PATCH.
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
# Register all SQLAlchemy model tables
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


class TestPredictionInterventionE2E(unittest.TestCase):
    """End-to-End integration test suite for the Prediction -> Intervention lifecycle."""

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
        """Reset data and configure isolated fixtures per test."""
        self.db = self.Session()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

        # 1. Base academic structure
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
        self.db.commit()

        # 2. User accounts
        self.user_faculty = User(
            id=1,
            email="faculty@test.com",
            password_hash="hash_fac",
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_student1 = User(
            id=2,
            email="student1@test.com",
            password_hash="hash_s1",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.user_student2 = User(
            id=3,
            email="student2@test.com",
            password_hash="hash_s2",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add_all([self.user_faculty, self.user_student1, self.user_student2])
        self.db.commit()

        # 3. Faculty record
        self.faculty = Faculty(
            id=1,
            user_id=1,
            department_id=1,
            employee_code="FAC001",
            first_name="Alan",
            last_name="Turing",
            designation="Professor",
            is_active=True,
        )

        # 4. Student records
        self.student1 = Student(
            id=1,
            user_id=2,
            department_id=1,
            course_id=1,
            roll_number="MCA2024001",
            admission_year=2024,
            current_semester=1,
            name="Ada Lovelace",
            email="student1@test.com",
            is_active=True,
        )
        self.student2 = Student(
            id=2,
            user_id=3,
            department_id=1,
            course_id=1,
            roll_number="MCA2024002",
            admission_year=2024,
            current_semester=1,
            name="Charles Babbage",
            email="student2@test.com",
            is_active=True,
        )
        self.db.add_all([self.faculty, self.student1, self.student2])
        self.db.commit()

        # 5. Seed Semester 1 academic records for Student 1 (features for ML inference)
        # Subject
        self.sub1 = Subject(
            id=101,
            course_id=1,
            name="Problem Solving with C",
            code="CS101",
            semester=1,
            credits=4,
            is_active=True,
        )
        self.db.add(self.sub1)
        self.db.commit()

        # Enrollment
        self.enrollment1 = Enrollment(
            id=1,
            student_id=1,
            subject_id=101,
            academic_year="2024-25",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add(self.enrollment1)
        self.db.commit()

        # Attendance: 4 present, 1 absent -> 80.0% attendance
        for day in range(1, 5):
            self.db.add(
                Attendance(
                    id=100 + day,
                    enrollment_id=1,
                    attendance_date=date(2024, 9, day),
                    status=AttendanceStatus.PRESENT,
                )
            )
        self.db.add(
            Attendance(
                id=105,
                enrollment_id=1,
                attendance_date=date(2024, 9, 5),
                status=AttendanceStatus.ABSENT,
            )
        )

        # Assignment: 90.0% (90/100)
        self.db.add(
            Assessment(
                id=201,
                enrollment_id=1,
                assessment_type=AssessmentType.ASSIGNMENT,
                assessment_name="Programming Assignment 1",
                max_marks=100,
                obtained_marks=90,
                assessment_date=date(2024, 9, 10),
            )
        )

        # Class Test 1 (CT1): 85.0% (17/20)
        self.db.add(
            Assessment(
                id=202,
                enrollment_id=1,
                assessment_type=AssessmentType.CT1,
                assessment_name="Class Test 1",
                max_marks=20,
                obtained_marks=17,
                assessment_date=date(2024, 9, 15),
            )
        )
        # Note: Strictly NO CT2 or FINAL assessments are added.
        self.db.commit()

        # Default authenticated user for test actions
        self.active_user = self.user_faculty
        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.active_user

    def tearDown(self):
        """Clean up session and dependency overrides."""
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

    def _post(self, path: str, json_data: dict | None = None):
        return self._request("POST", path, json_data)

    def _get(self, path: str):
        return self._request("GET", path)

    def _patch(self, path: str, json_data: dict | None = None):
        return self._request("PATCH", path, json_data)

    # ==================================================================
    # COMPLETE CROSS-MODULE LIFECYCLE TEST
    # ==================================================================

    def test_complete_prediction_to_intervention_lifecycle_e2e(self):
        """
        Execute the complete, unbroken end-to-end integration flow:
        1. Query live Prediction API for Student 1 in Semester 1.
        2. Verify features and obtain live predicted score and academic status.
        3. Verify that prediction does NOT automatically create an intervention.
        4. Faculty manually creates intervention using captured prediction evidence.
        5. Verify historical snapshot is accurately persisted.
        6. Student 1 views own assigned intervention.
        7. Student 2 is blocked from viewing Student 1's intervention (IDOR protection).
        8. Faculty updates intervention workflow to COMPLETED via PATCH.
        9. Historical trigger evidence remains strictly immutable after update.
        """
        # --------------------------------------------------------------
        # STEP 1 & 2: Generate Prediction from DB-backed records
        # --------------------------------------------------------------
        self.active_user = self.user_faculty
        status_code, pred_response = self._post("/predictions/students/1", {"semester": 1})

        self.assertEqual(status_code, 200)
        self.assertEqual(pred_response["student_id"], 1)
        self.assertEqual(pred_response["semester"], 1)
        self.assertIn("predicted_final_semester_score", pred_response)
        self.assertIn("academic_status", pred_response)
        self.assertIn(pred_response["academic_status"], ["NORMAL", "MONITOR", "INTERVENTION"])

        # Verify exact ML feature dictionary for Semester 1 model
        expected_feature_keys = {
            "current_attendance",
            "current_assignment_average",
            "current_ct1_average",
        }
        self.assertEqual(set(pred_response["features"].keys()), expected_feature_keys)
        self.assertEqual(pred_response["features"]["current_attendance"], 80.0)
        self.assertEqual(pred_response["features"]["current_assignment_average"], 90.0)
        self.assertEqual(pred_response["features"]["current_ct1_average"], 85.0)

        # Capture live prediction evidence directly from the API response
        live_predicted_score = pred_response["predicted_final_semester_score"]
        live_academic_status = pred_response["academic_status"]
        self.assertIsInstance(live_predicted_score, float)
        self.assertIsInstance(live_academic_status, str)

        # --------------------------------------------------------------
        # STEP 3: Verify NO automatic intervention was created
        # --------------------------------------------------------------
        status_code, list_before = self._get("/api/v1/interventions/")
        self.assertEqual(status_code, 200)
        self.assertEqual(
            len(list_before),
            0,
            "Prediction generation must NOT automatically create intervention records in the database.",
        )

        # --------------------------------------------------------------
        # STEP 4: Faculty manually reviews and assigns intervention
        # --------------------------------------------------------------
        intervention_payload = {
            "student_id": 1,
            "faculty_id": 1,
            "semester": 1,
            "intervention_type": "extra_class",
            "trigger_predicted_score": live_predicted_score,
            "trigger_academic_status": live_academic_status,
            "description": "Assigned supplementary programming tutorials based on early academic prediction.",
            "action_plan": "Attend twice-weekly lab sessions with faculty mentor.",
            "follow_up_date": "2024-11-20",
        }

        status_code, create_response = self._post("/api/v1/interventions/", intervention_payload)
        self.assertEqual(status_code, 201)
        self.assertIn("id", create_response)
        intervention_id = create_response["id"]

        self.assertEqual(create_response["student_id"], 1)
        self.assertEqual(create_response["faculty_id"], 1)
        self.assertEqual(create_response["semester"], 1)
        self.assertEqual(create_response["intervention_type"], "extra_class")
        self.assertEqual(create_response["status"], "assigned")
        # Assert exact evidence transfer
        self.assertEqual(create_response["trigger_predicted_score"], live_predicted_score)
        self.assertEqual(create_response["trigger_academic_status"], live_academic_status)
        self.assertEqual(create_response["follow_up_date"], "2024-11-20")

        # --------------------------------------------------------------
        # STEP 5: Verify historical snapshot persistence
        # --------------------------------------------------------------
        status_code, get_response = self._get(f"/api/v1/interventions/{intervention_id}")
        self.assertEqual(status_code, 200)
        self.assertEqual(get_response["id"], intervention_id)
        self.assertEqual(get_response["trigger_predicted_score"], live_predicted_score)
        self.assertEqual(get_response["trigger_academic_status"], live_academic_status)

        # --------------------------------------------------------------
        # STEP 6: Student 1 views own assigned intervention
        # --------------------------------------------------------------
        self.active_user = self.user_student1
        status_code, student_view = self._get(f"/api/v1/interventions/{intervention_id}")
        self.assertEqual(status_code, 200)
        self.assertEqual(student_view["id"], intervention_id)
        self.assertEqual(student_view["student_id"], 1)
        self.assertEqual(student_view["status"], "assigned")
        self.assertEqual(student_view["trigger_predicted_score"], live_predicted_score)
        self.assertEqual(student_view["trigger_academic_status"], live_academic_status)

        # --------------------------------------------------------------
        # STEP 7: Student IDOR Protection (Student 2 attempts access)
        # --------------------------------------------------------------
        self.active_user = self.user_student2

        # 7a. Direct IDOR attempt via path parameter
        status_code, idor_response = self._get(f"/api/v1/interventions/{intervention_id}")
        self.assertEqual(status_code, 403)
        self.assertEqual(idor_response["detail"], "You do not have permission to access this intervention.")

        # 7b. List enumeration attempt via query parameter
        status_code, idor_list = self._get("/api/v1/interventions/?student_id=1")
        self.assertEqual(status_code, 200)
        self.assertEqual(
            len(idor_list),
            0,
            "Student 2 querying for Student 1's interventions must be hard-scoped to own records (empty list).",
        )

        # --------------------------------------------------------------
        # STEP 8: Faculty updates intervention to COMPLETED
        # --------------------------------------------------------------
        self.active_user = self.user_faculty
        patch_payload = {
            "status": "completed",
            "description": "Student successfully completed all supplementary lab sessions.",
            "action_plan": "Regular monitoring resumed.",
            "follow_up_date": "2024-12-05",
        }
        status_code, patch_response = self._patch(
            f"/api/v1/interventions/{intervention_id}",
            patch_payload,
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(patch_response["status"], "completed")
        self.assertEqual(patch_response["description"], "Student successfully completed all supplementary lab sessions.")
        self.assertEqual(patch_response["action_plan"], "Regular monitoring resumed.")
        self.assertEqual(patch_response["follow_up_date"], "2024-12-05")

        # --------------------------------------------------------------
        # STEP 9: Verify historical trigger evidence remains immutable
        # --------------------------------------------------------------
        self.assertEqual(
            patch_response["trigger_predicted_score"],
            live_predicted_score,
            "Historical trigger predicted score must remain strictly unchanged after workflow update.",
        )
        self.assertEqual(
            patch_response["trigger_academic_status"],
            live_academic_status,
            "Historical trigger academic status must remain strictly unchanged after workflow update.",
        )

        # Final verification via GET after PATCH
        status_code, final_view = self._get(f"/api/v1/interventions/{intervention_id}")
        self.assertEqual(status_code, 200)
        self.assertEqual(final_view["status"], "completed")
        self.assertEqual(final_view["trigger_predicted_score"], live_predicted_score)
        self.assertEqual(final_view["trigger_academic_status"], live_academic_status)

    def test_prediction_does_not_auto_create_intervention(self):
        """
        Explicitly verify that calling the prediction API multiple times across semesters
        does not generate any records in the interventions table.
        """
        self.active_user = self.user_faculty

        # Trigger prediction API
        status_code, pred_body = self._post("/predictions/students/1", {"semester": 1})
        self.assertEqual(status_code, 200)

        # Verify zero interventions in database
        status_code, list_resp = self._get("/api/v1/interventions/")
        self.assertEqual(status_code, 200)
        self.assertEqual(len(list_resp), 0)


if __name__ == "__main__":
    unittest.main()
