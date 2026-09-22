"""
Automated tests for VCIS 3.0 ML Prediction Router (app/routers/predictions.py).

Validates:
1. Semester 1 successful API prediction (Model 1, 3 features).
2. Semester 2 successful API prediction (Model 2, 5 features).
3. Semester 3 successful API prediction (verifying generic 2–4 dispatch).
4. Invalid semester (0, 5, negative, non-int) is rejected with HTTP 422.
5. Missing student returns HTTP 404.
6. Insufficient academic data returns HTTP 422.
7. CT2 and FINAL assessment records do NOT leak into features or predictions.
8. Response contains correct model metadata (model_version, model_type, scenario).
9. Response feature dictionary keys exactly match the fixed ML contract.
10. Router delegates cleanly and passes features directly to prediction_service.
11. Invalid student ID (<= 0) returns HTTP 400.
12. Both route aliases (/predictions/... and /api/v1/predictions/...) succeed.
"""

import asyncio
import json
import os
import sys
import unittest
from datetime import date
from unittest.mock import patch

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

from app.models.course import Course
from app.models.student import Student
from app.models.subject import Subject
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assessment import Assessment, AssessmentType
from app.models.user import User, UserRole

from app.main import app
from app.database import get_db
from app.core.dependencies import get_current_user


class TestPredictionRouter(unittest.TestCase):
    """Integration test suite for the FastAPI prediction API endpoint."""

    @classmethod
    def setUpClass(cls):
        """Set up in-memory SQLite engine with thread-safe StaticPool."""
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        """Dispose of the engine at test class completion."""
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        """Reset data and configure FastAPI dependency overrides per test."""
        # Clear tables
        for table in reversed(Base.metadata.sorted_tables):
            self.engine.execute(table.delete()) if hasattr(self.engine, "execute") else None

        self.db = self.Session()
        # Clean all data using session
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

        # Mock authenticated user
        self.mock_user = User(
            id=1,
            email="admin@test.com",
            password_hash="fakehash",
            role=UserRole.ADMIN,
            is_active=True,
        )

        app.dependency_overrides[get_db] = lambda: self.db
        app.dependency_overrides[get_current_user] = lambda: self.mock_user

    def tearDown(self):
        """Clean up session and dependency overrides."""
        self.db.close()
        app.dependency_overrides.clear()

    # ------------------------------------------------------------------
    # Pure ASGI Request Helper (No external httpx dependency required)
    # ------------------------------------------------------------------

    def _post(self, path: str, json_data: dict | None = None) -> tuple[int, dict]:
        """Execute a POST request against the FastAPI ASGI application."""
        body = json.dumps(json_data).encode("utf-8") if json_data is not None else b""
        headers = [
            (b"content-type", b"application/json"),
            (b"authorization", b"Bearer test-token"),
        ]
        status_code = None
        response_body = []

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
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

    # ------------------------------------------------------------------
    # Helper Fixture Creators
    # ------------------------------------------------------------------

    def _create_student(
        self,
        student_id: int = 1,
        current_semester: int = 1,
        course_id: int = 1,
        total_semesters: int = 4,
    ) -> Student:
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if course is None:
            course = Course(
                id=course_id,
                department_id=1,
                name="MCA" if course_id == 1 else f"Course {course_id}",
                code="MCA" if course_id == 1 else f"CRS{course_id}",
                duration_years=2 if total_semesters <= 4 else 4,
                total_semesters=total_semesters,
                is_active=True,
            )
            self.db.add(course)
            self.db.commit()

        student = Student(
            id=student_id,
            user_id=student_id,
            department_id=1,
            course_id=course_id,
            roll_number=f"ROLL_{student_id}",
            admission_year=2024,
            current_semester=current_semester,
            name=f"Student {student_id}",
            email=f"student{student_id}@test.com",
            is_active=True,
        )
        self.db.add(student)
        self.db.commit()
        return student

    def _create_subject(self, subject_id: int, semester: int, name: str = "Subject") -> Subject:
        subject = Subject(
            id=subject_id,
            course_id=1,
            name=f"{name} {subject_id}",
            code=f"SUB_{subject_id}",
            semester=semester,
            credits=4,
            is_active=True,
        )
        self.db.add(subject)
        self.db.commit()
        return subject

    def _create_enrollment(
        self,
        enrollment_id: int,
        student_id: int,
        subject_id: int,
        status: EnrollmentStatus = EnrollmentStatus.ENROLLED,
    ) -> Enrollment:
        enrollment = Enrollment(
            id=enrollment_id,
            student_id=student_id,
            subject_id=subject_id,
            academic_year="2024-25",
            status=status,
        )
        self.db.add(enrollment)
        self.db.commit()
        return enrollment

    def _create_attendance(
        self,
        attendance_id: int,
        enrollment_id: int,
        status: AttendanceStatus,
        day: int = 1,
    ) -> Attendance:
        record = Attendance(
            id=attendance_id,
            enrollment_id=enrollment_id,
            attendance_date=date(2024, 9, day),
            status=status,
        )
        self.db.add(record)
        self.db.commit()
        return record

    def _create_assessment(
        self,
        assessment_id: int,
        enrollment_id: int,
        assessment_type: AssessmentType,
        assessment_name: str,
        max_marks: int,
        obtained_marks: int,
    ) -> Assessment:
        record = Assessment(
            id=assessment_id,
            enrollment_id=enrollment_id,
            assessment_type=assessment_type,
            assessment_name=assessment_name,
            max_marks=max_marks,
            obtained_marks=obtained_marks,
            assessment_date=date(2024, 9, 15),
        )
        self.db.add(record)
        self.db.commit()
        return record

    # ==================================================================
    # TEST 1 — SEMESTER 1 SUCCESSFUL API PREDICTION
    # ==================================================================

    def test_01_semester_1_successful_prediction(self):
        """
        Verify POST /predictions/students/{id} for Semester 1:
        Returns 200 OK, predicted_final_semester_score rounded to 2 decimals,
        metadata for Semester 1, and exact 3 features.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)

        # 4 PRESENT, 1 ABSENT -> 80.0%
        for i in range(1, 5):
            self._create_attendance(attendance_id=i, enrollment_id=1, status=AttendanceStatus.PRESENT, day=i)
        self._create_attendance(attendance_id=5, enrollment_id=1, status=AttendanceStatus.ABSENT, day=5)

        # Assignment: 18 / 20 -> 90.0%
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst 1",
            max_marks=20,
            obtained_marks=18,
        )
        # CT1: 17 / 20 -> 85.0%
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=17,
        )

        status_code, body = self._post("/predictions/students/1", {"semester": 1})

        self.assertEqual(status_code, 200)
        self.assertEqual(body["student_id"], 1)
        self.assertEqual(body["semester"], 1)
        self.assertEqual(body["model_version"], "1.0")
        self.assertEqual(body["model_type"], "LinearRegression")
        self.assertEqual(body["scenario"], "Semester 1")
        self.assertEqual(body["predicted_final_semester_score"], 88.48)
        self.assertEqual(
            body["features"],
            {
                "current_attendance": 80.0,
                "current_assignment_average": 90.0,
                "current_ct1_average": 85.0,
            },
        )

    # ==================================================================
    # TEST 2 — SEMESTER 2 SUCCESSFUL API PREDICTION
    # ==================================================================

    def test_02_semester_2_successful_prediction(self):
        """
        Verify POST /predictions/students/{id} for Semester 2:
        Returns 200 OK, predicted_final_semester_score rounded to 2 decimals,
        metadata for Semesters 2+, and exact 5 features.
        """
        self._create_student(student_id=2, current_semester=2)

        # Sem 1 (previous): completed enrollment, attendance 100%, final exam 82%
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=2, subject_id=101, status=EnrollmentStatus.COMPLETED)
        for i in range(1, 5):
            self._create_attendance(attendance_id=i, enrollment_id=1, status=AttendanceStatus.PRESENT, day=i)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Sem1 Final",
            max_marks=100,
            obtained_marks=82,
        )

        # Sem 2 (current): attendance 80%, assignment 80%, CT1 75%
        self._create_subject(subject_id=201, semester=2)
        self._create_enrollment(enrollment_id=2, student_id=2, subject_id=201, status=EnrollmentStatus.ENROLLED)
        for i in range(5, 9):
            self._create_attendance(attendance_id=i, enrollment_id=2, status=AttendanceStatus.PRESENT, day=i)
        self._create_attendance(attendance_id=9, enrollment_id=2, status=AttendanceStatus.ABSENT, day=9)

        self._create_assessment(
            assessment_id=2,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Sem2 Asst",
            max_marks=50,
            obtained_marks=40,
        )
        self._create_assessment(
            assessment_id=3,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="Sem2 CT1",
            max_marks=20,
            obtained_marks=15,
        )

        status_code, body = self._post("/predictions/students/2", {"semester": 2})

        self.assertEqual(status_code, 200)
        self.assertEqual(body["student_id"], 2)
        self.assertEqual(body["semester"], 2)
        self.assertEqual(body["model_version"], "1.0")
        self.assertEqual(body["model_type"], "LinearRegression")
        self.assertEqual(body["scenario"], "Semesters 2+")
        self.assertEqual(body["predicted_final_semester_score"], 79.52)
        self.assertEqual(
            body["features"],
            {
                "previous_semester_score": 82.0,
                "previous_semester_attendance": 100.0,
                "current_attendance": 80.0,
                "current_assignment_average": 80.0,
                "current_ct1_average": 75.0,
            },
        )

    # ==================================================================
    # TEST 3 — SEMESTER 3 SUCCESSFUL API PREDICTION (2-4 DISPATCH)
    # ==================================================================

    def test_03_semester_3_successful_prediction(self):
        """
        Verify that requesting semester=3 correctly triggers the Model 2 pipeline
        (using previous semester = 2 and current semester = 3).
        """
        self._create_student(student_id=3, current_semester=3)

        # Sem 2 (previous): completed, attendance 100%, final 82%
        self._create_subject(subject_id=201, semester=2)
        self._create_enrollment(enrollment_id=1, student_id=3, subject_id=201, status=EnrollmentStatus.COMPLETED)
        for i in range(1, 5):
            self._create_attendance(attendance_id=i, enrollment_id=1, status=AttendanceStatus.PRESENT, day=i)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Sem2 Final",
            max_marks=100,
            obtained_marks=82,
        )

        # Sem 3 (current): attendance 80%, assignment 80%, CT1 75%
        self._create_subject(subject_id=301, semester=3)
        self._create_enrollment(enrollment_id=2, student_id=3, subject_id=301, status=EnrollmentStatus.ENROLLED)
        for i in range(5, 9):
            self._create_attendance(attendance_id=i, enrollment_id=2, status=AttendanceStatus.PRESENT, day=i)
        self._create_attendance(attendance_id=9, enrollment_id=2, status=AttendanceStatus.ABSENT, day=9)

        self._create_assessment(
            assessment_id=2,
            enrollment_id=2,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Sem3 Asst",
            max_marks=50,
            obtained_marks=40,
        )
        self._create_assessment(
            assessment_id=3,
            enrollment_id=2,
            assessment_type=AssessmentType.CT1,
            assessment_name="Sem3 CT1",
            max_marks=20,
            obtained_marks=15,
        )

        status_code, body = self._post("/predictions/students/3", {"semester": 3})

        self.assertEqual(status_code, 200)
        self.assertEqual(body["student_id"], 3)
        self.assertEqual(body["semester"], 3)
        self.assertEqual(body["scenario"], "Semesters 2+")
        self.assertEqual(len(body["features"]), 5)

    # ==================================================================
    # TEST 4 — INVALID SEMESTER REJECTED
    # ==================================================================

    def test_04_invalid_semester_rejected(self):
        """
        Verify that out-of-range or malformed semesters (0, 5, -1, 'spring')
        are rejected with HTTP 422 Unprocessable Entity.
        """
        self._create_student(student_id=1, current_semester=1)

        invalid_semesters = [0, 5, -1, 10, "invalid"]
        for sem in invalid_semesters:
            status_code, body = self._post("/predictions/students/1", {"semester": sem})
            self.assertEqual(
                status_code,
                422,
                f"Expected 422 for semester={sem}, got {status_code}: {body}",
            )

    # ==================================================================
    # TEST 5 — MISSING STUDENT RETURNS 404
    # ==================================================================

    def test_05_missing_student_returns_404(self):
        """
        Verify that requesting prediction for a non-existent student ID returns
        HTTP 404 Not Found with a descriptive message.
        """
        status_code, body = self._post("/predictions/students/99999", {"semester": 1})

        self.assertEqual(status_code, 404)
        self.assertIn("detail", body)
        self.assertIn("99999", body["detail"])

    # ==================================================================
    # TEST 6 — INSUFFICIENT DATA RETURNS 422
    # ==================================================================

    def test_06_insufficient_data_returns_422(self):
        """
        Verify that when a student exists but lacks required academic records
        (e.g. no attendance records), HTTP 422 Unprocessable Entity is returned.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)
        # No attendance or assessments added!

        status_code, body = self._post("/predictions/students/1", {"semester": 1})

        self.assertEqual(status_code, 422)
        self.assertIn("detail", body)
        self.assertIn("attendance", body["detail"].lower())

    # ==================================================================
    # TEST 7 — CT2 AND FINAL DO NOT AFFECT THE PREDICTION RESPONSE
    # ==================================================================

    def test_07_ct2_and_final_do_not_leak_into_api_prediction(self):
        """
        Verify that adding extreme CT2 and FINAL assessment records does not alter
        either the features dictionary or the predicted score in the API response.
        """
        self._create_student(student_id=4, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=4, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst 1",
            max_marks=20,
            obtained_marks=18,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1 1",
            max_marks=20,
            obtained_marks=16,
        )

        # Baseline prediction
        status_before, body_before = self._post("/predictions/students/4", {"semester": 1})
        self.assertEqual(status_before, 200)

        # Add extreme CT2 and FINAL records
        self._create_assessment(
            assessment_id=3,
            enrollment_id=1,
            assessment_type=AssessmentType.CT2,
            assessment_name="CT2 Extreme",
            max_marks=20,
            obtained_marks=0,
        )
        self._create_assessment(
            assessment_id=4,
            enrollment_id=1,
            assessment_type=AssessmentType.FINAL,
            assessment_name="Final Exam Extreme",
            max_marks=100,
            obtained_marks=0,
        )

        # Post-addition prediction
        status_after, body_after = self._post("/predictions/students/4", {"semester": 1})
        self.assertEqual(status_after, 200)

        # Strict assertion of equivalence
        self.assertEqual(body_before["features"], body_after["features"])
        self.assertEqual(
            body_before["predicted_final_semester_score"],
            body_after["predicted_final_semester_score"],
        )

    # ==================================================================
    # TEST 8 — RESPONSE CONTAINS MODEL METADATA
    # ==================================================================

    def test_08_response_contains_model_metadata(self):
        """
        Verify that the response explicitly includes model metadata fields:
        model_version, model_type, and scenario.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=18,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )

        status_code, body = self._post("/predictions/students/1", {"semester": 1})

        self.assertEqual(status_code, 200)
        self.assertIn("model_version", body)
        self.assertIn("model_type", body)
        self.assertIn("scenario", body)
        self.assertEqual(body["model_version"], "1.0")
        self.assertEqual(body["model_type"], "LinearRegression")
        self.assertEqual(body["scenario"], "Semester 1")

    # ==================================================================
    # TEST 9 — RESPONSE FEATURE KEYS EXACTLY MATCH ML CONTRACT
    # ==================================================================

    def test_09_exact_feature_keys_match_ml_contract(self):
        """
        Verify that the features object contains exactly the ML contract feature names:
        - Semester 1: current_attendance, current_assignment_average, current_ct1_average
        - No extra metadata (student_id, semester, final_semester_score) in features.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=18,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )

        status_code, body = self._post("/predictions/students/1", {"semester": 1})

        self.assertEqual(status_code, 200)
        feature_keys = set(body["features"].keys())
        expected_keys = {
            "current_attendance",
            "current_assignment_average",
            "current_ct1_average",
        }
        self.assertEqual(feature_keys, expected_keys)
        self.assertNotIn("student_id", feature_keys)
        self.assertNotIn("semester", feature_keys)
        self.assertNotIn("final_semester_score", feature_keys)

    # ==================================================================
    # TEST 10 — ROUTER PASSES EXTRACTED FEATURES DIRECTLY TO PREDICTION_SERVICE
    # ==================================================================

    def test_10_router_passes_features_directly_without_transformation(self):
        """
        Verify that the router does not modify the dictionary returned by
        feature_service.extract_ml_features before passing it to
        prediction_service.predict_final_score.
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=18,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )

        from app.routers import predictions as pred_module

        with patch.object(pred_module, "predict_final_score", wraps=pred_module.predict_final_score) as mock_predict:
            status_code, body = self._post("/predictions/students/1", {"semester": 1})
            self.assertEqual(status_code, 200)
            mock_predict.assert_called_once()
            called_semester = mock_predict.call_args[1].get("semester")
            called_features = mock_predict.call_args[1].get("features")
            self.assertEqual(called_semester, 1)
            self.assertEqual(called_features, body["features"])

    # ==================================================================
    # TEST 11 — INVALID STUDENT ID (<= 0) RETURNS 400
    # ==================================================================

    def test_11_invalid_student_id_returns_400(self):
        """
        Verify that student IDs <= 0 return HTTP 400 Bad Request.
        """
        status_0, body_0 = self._post("/predictions/students/0", {"semester": 1})
        self.assertEqual(status_0, 400)
        self.assertIn("Invalid student ID", body_0["detail"])

        status_neg, body_neg = self._post("/predictions/students/-5", {"semester": 1})
        self.assertEqual(status_neg, 400)
        self.assertIn("Invalid student ID", body_neg["detail"])

    # ==================================================================
    # TEST 12 — ROUTE ALIASES (/predictions/students and /api/v1/predictions/students)
    # ==================================================================

    def test_12_route_aliases_both_accessible(self):
        """
        Verify that both endpoint paths work identically:
        - /predictions/students/{id}
        - /api/v1/predictions/students/{id}
        """
        self._create_student(student_id=1, current_semester=1)
        self._create_subject(subject_id=101, semester=1)
        self._create_enrollment(enrollment_id=1, student_id=1, subject_id=101)
        self._create_attendance(attendance_id=1, enrollment_id=1, status=AttendanceStatus.PRESENT)
        self._create_assessment(
            assessment_id=1,
            enrollment_id=1,
            assessment_type=AssessmentType.ASSIGNMENT,
            assessment_name="Asst",
            max_marks=20,
            obtained_marks=18,
        )
        self._create_assessment(
            assessment_id=2,
            enrollment_id=1,
            assessment_type=AssessmentType.CT1,
            assessment_name="CT1",
            max_marks=20,
            obtained_marks=16,
        )

        status_1, body_1 = self._post("/predictions/students/1", {"semester": 1})
        status_2, body_2 = self._post("/api/v1/predictions/students/1", {"semester": 1})

        self.assertEqual(status_1, 200)
        self.assertEqual(status_2, 200)
        self.assertEqual(body_1, body_2)


if __name__ == "__main__":
    unittest.main()
