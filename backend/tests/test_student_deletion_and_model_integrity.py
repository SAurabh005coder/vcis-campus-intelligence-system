"""
VCIS 3.0 — Student Deletion Integrity & User Model Mapping Tests

Validates:
1. User model has exactly one 'updated_at' column and attribute.
2. User model can be created, committed, and updated cleanly.
3. DELETE /api/v1/students/{student_id} authorization:
   - Anonymous -> 401 Unauthorized
   - Student -> 403 Forbidden
   - Faculty -> 403 Forbidden
   - HOD -> 403 Forbidden
   - Admin -> Allowed (204 or 409)
4. Deletion conflict handling:
   - Deleting nonexistent student -> 404 Not Found
   - Deleting student with dependent enrollments -> 409 Conflict
   - Clear conflict detail message returned
   - Session remains usable following rollback
   - Student and enrollment records remain intact following 409
   - Deleting student with no dependent records -> 204 No Content
   - Student successfully removed from database after 204
"""

import asyncio
from datetime import datetime, timezone
import json
import os
import sys
import unittest

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-student-deletion-integrity-secret-key-12345"

from sqlalchemy import create_engine, inspect
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

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.models.course import Course
from app.models.department import Department
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.faculty import Faculty
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User, UserRole


class TestUserModelIntegrity(unittest.TestCase):
    """Verifies User model ORM mapping and single updated_at column."""

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

    def test_user_model_has_exactly_one_updated_at_column(self):
        """User model table definition must declare 'updated_at' exactly once."""
        columns = [c.name for c in User.__table__.columns]
        updated_at_count = columns.count("updated_at")
        self.assertEqual(
            updated_at_count,
            1,
            f"Expected exactly 1 updated_at column in User table, found {updated_at_count}",
        )

    def test_user_model_has_exactly_one_updated_at_mapper_attribute(self):
        """User ORM mapper must have exactly one attribute named 'updated_at'."""
        mapper = inspect(User)
        self.assertIn("updated_at", mapper.column_attrs)
        # Verify it has onupdate configured
        col = User.__table__.c.updated_at
        self.assertIsNotNone(col.onupdate)

    def test_user_model_crud_lifecycle(self):
        """User can be created, queried, and updated cleanly."""
        db = self.Session()
        user = User(
            email="model_test@test.com",
            password_hash="testhash123",
            role=UserRole.STUDENT,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        self.assertIsNotNone(user.id)
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

        # Update user
        user.email = "model_updated@test.com"
        db.commit()
        db.refresh(user)
        self.assertEqual(user.email, "model_updated@test.com")
        db.close()


class TestStudentDeletionIntegrity(unittest.TestCase):
    """Test suite verifying RBAC and referential integrity conflict handling on student deletion."""

    @classmethod
    def setUpClass(cls):
        # Use SQLite with foreign keys enforced (PRAGMA foreign_keys = ON)
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        from sqlalchemy import event
        @event.listens_for(cls.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

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

        # Department -> Course -> Subject (in dependency order)
        self.dept = Department(id=1, name="Computer Science", code="CSE", is_active=True)
        self.db.add(self.dept)
        self.db.commit()

        self.course = Course(id=1, department_id=1, name="B.Tech CSE", code="BTCSE", duration_years=4, total_semesters=8, is_active=True)
        self.db.add(self.course)
        self.db.commit()

        self.subject = Subject(id=101, course_id=1, name="Data Structures", code="CS101", semester=1, credits=4, is_active=True)
        self.db.add(self.subject)
        self.db.commit()

        # Users for each role
        self.user_admin = User(id=1, email="admin@test.com", password_hash="hash", role=UserRole.ADMIN, is_active=True)
        self.user_faculty = User(id=2, email="faculty@test.com", password_hash="hash", role=UserRole.FACULTY, is_active=True)
        self.user_hod = User(id=3, email="hod@test.com", password_hash="hash", role=UserRole.HOD, is_active=True)
        self.user_student = User(id=4, email="student@test.com", password_hash="hash", role=UserRole.STUDENT, is_active=True)
        self.user_student_standalone = User(id=5, email="standalone@test.com", password_hash="hash", role=UserRole.STUDENT, is_active=True)

        self.db.add_all([
            self.user_admin,
            self.user_faculty,
            self.user_hod,
            self.user_student,
            self.user_student_standalone,
        ])
        self.db.commit()

        # Faculty profile for HOD
        self.faculty_hod = Faculty(
            id=1,
            user_id=3,
            department_id=1,
            employee_code="HOD-001",
            first_name="HOD",
            last_name="CSE",
            designation="Head of Department",
            is_active=True,
        )
        self.db.add(self.faculty_hod)

        # Student 1: Has an enrollment (dependent record)
        self.student_with_enrollment = Student(
            id=101,
            user_id=4,
            department_id=1,
            course_id=1,
            roll_number="CSE101",
            admission_year=2023,
            current_semester=1,
            name="Alice Dependent",
            email="student@test.com",
            is_active=True,
        )

        # Student 2: Standalone (no enrollments)
        self.student_standalone = Student(
            id=102,
            user_id=5,
            department_id=1,
            course_id=1,
            roll_number="CSE102",
            admission_year=2023,
            current_semester=1,
            name="Bob Standalone",
            email="standalone@test.com",
            is_active=True,
        )

        self.db.add_all([self.student_with_enrollment, self.student_standalone])
        self.db.commit()

        # Enrollment for student 101
        self.enrollment = Enrollment(
            id=1001,
            student_id=101,
            subject_id=101,
            academic_year="2023-2024",
            status=EnrollmentStatus.ENROLLED,
        )
        self.db.add(self.enrollment)
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

    def _delete(self, path: str, user: User | None = None):
        self.active_user = user

        scope = {
            "type": "http",
            "method": "DELETE",
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

    # -------------------------------------------------------------------------
    # RBAC Tests on DELETE /api/v1/students/{student_id}
    # -------------------------------------------------------------------------

    def test_anonymous_delete_fails(self):
        """Anonymous user cannot delete student -> 401 Unauthorized."""
        code, _ = self._delete("/api/v1/students/102", user=None)
        self.assertEqual(code, 401)

    def test_student_delete_fails(self):
        """Student cannot delete student -> 403 Forbidden."""
        code, _ = self._delete("/api/v1/students/102", user=self.user_student)
        self.assertEqual(code, 403)

    def test_faculty_delete_fails(self):
        """Faculty cannot delete student -> 403 Forbidden."""
        code, _ = self._delete("/api/v1/students/102", user=self.user_faculty)
        self.assertEqual(code, 403)

    def test_hod_delete_fails(self):
        """HOD cannot delete student -> 403 Forbidden."""
        code, _ = self._delete("/api/v1/students/102", user=self.user_hod)
        self.assertEqual(code, 403)

    # -------------------------------------------------------------------------
    # Deletion Integrity and Conflict Tests
    # -------------------------------------------------------------------------

    def test_admin_delete_nonexistent_student_returns_404(self):
        """Admin deleting nonexistent student -> 404 Not Found."""
        code, data = self._delete("/api/v1/students/99999", user=self.user_admin)
        self.assertEqual(code, 404)
        self.assertIn("Student not found", data.get("detail", ""))

    def test_admin_delete_student_with_enrollment_returns_409_conflict(self):
        """Admin deleting student with active enrollments -> 409 Conflict with clear detail."""
        code, data = self._delete("/api/v1/students/101", user=self.user_admin)
        self.assertEqual(code, 409)
        self.assertIn("Cannot delete student with existing academic records or enrollments", data.get("detail", ""))

    def test_database_session_and_records_intact_after_failed_deletion(self):
        """Session remains healthy and student + enrollment remain intact after 409."""
        code, data = self._delete("/api/v1/students/101", user=self.user_admin)
        self.assertEqual(code, 409)

        # Verify records are intact in the database
        student = self.db.query(Student).filter(Student.id == 101).first()
        self.assertIsNotNone(student, "Student 101 should still exist in database")
        self.assertEqual(student.name, "Alice Dependent")

        enrollment = self.db.query(Enrollment).filter(Enrollment.id == 1001).first()
        self.assertIsNotNone(enrollment, "Enrollment 1001 should still exist in database")
        self.assertEqual(enrollment.student_id, 101)

        # Verify session can execute further queries without error
        count = self.db.query(Student).count()
        self.assertEqual(count, 2)

    def test_admin_delete_standalone_student_succeeds(self):
        """Admin deleting student without dependent records -> 204 No Content."""
        code, _ = self._delete("/api/v1/students/102", user=self.user_admin)
        self.assertEqual(code, 204)

        # Verify record is deleted
        student = self.db.query(Student).filter(Student.id == 102).first()
        self.assertIsNone(student, "Student 102 should be deleted from database")


if __name__ == "__main__":
    unittest.main()
