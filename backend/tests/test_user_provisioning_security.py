"""
VCIS 3.0 — User Provisioning Security & Authorization Tests

Verifies that POST /api/v1/users/ strictly enforces Admin-only authorization:
1. Anonymous (unauthenticated) requests are rejected with HTTP 401.
2. Student callers are rejected with HTTP 403 Forbidden.
3. Faculty callers are rejected with HTTP 403 Forbidden.
4. HOD callers are rejected with HTTP 403 Forbidden.
5. Admin callers succeed with HTTP 201 Created.
6. Admin can provision accounts across roles (including student, faculty, hod, admin).
7. Invalid roles are rejected with HTTP 422 Unprocessable Entity.
8. Duplicate emails are rejected with HTTP 409 Conflict.
"""

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Enforce JWT key for test runtime before app imports
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-tests-32"

from app.base import Base
from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app
from app.models.user import User, UserRole


class TestUserProvisioningSecurity(unittest.TestCase):
    """Test suite verifying authorization rules on user provisioning endpoint."""

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

        # Seed authenticated role fixtures
        self.user_admin = User(
            id=1,
            email="admin@test.com",
            password_hash="hashed_pw_admin",
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.user_hod = User(
            id=2,
            email="hod@test.com",
            password_hash="hashed_pw_hod",
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_faculty = User(
            id=3,
            email="faculty@test.com",
            password_hash="hashed_pw_fac",
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_student = User(
            id=4,
            email="student@test.com",
            password_hash="hashed_pw_stud",
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add_all([
            self.user_admin,
            self.user_hod,
            self.user_faculty,
            self.user_student,
        ])
        self.db.commit()

        self.active_user = None
        app.dependency_overrides[get_db] = lambda: self.db

        def override_current_user():
            if self.active_user is None:
                # Simulate missing or invalid token
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
        json_data: dict | None = None,
        include_auth: bool = True,
    ) -> tuple[int, dict]:
        body = json.dumps(json_data).encode("utf-8") if json_data is not None else b""
        headers = [(b"content-type", b"application/json")]
        if include_auth:
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
            "method": method.upper(),
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

    def test_01_anonymous_user_creation_is_blocked(self):
        """Verify anonymous caller without authorization is rejected with HTTP 401."""
        self.active_user = None
        # Remove get_current_user override to test real dependency or test simulated unauthenticated
        payload = {
            "email": "rogue.admin@institution.edu",
            "password": "Password123!",
            "role": "admin",
        }
        status, data = self._request("POST", "/api/v1/users/", json_data=payload, include_auth=False)
        self.assertEqual(status, 401, f"Expected 401 Unauthorized for anonymous user, got: {status}")

    def test_02_student_user_creation_is_blocked(self):
        """Verify Student token cannot create any user accounts (HTTP 403 Forbidden)."""
        self.active_user = self.user_student
        payload = {
            "email": "elevated.student@institution.edu",
            "password": "Password123!",
            "role": "admin",
        }
        status, data = self._request("POST", "/api/v1/users/", json_data=payload)
        self.assertEqual(status, 403, f"Expected 403 Forbidden for student, got: {status}")

    def test_03_faculty_user_creation_is_blocked(self):
        """Verify Faculty token cannot create user accounts (HTTP 403 Forbidden)."""
        self.active_user = self.user_faculty
        payload = {
            "email": "faculty.created@institution.edu",
            "password": "Password123!",
            "role": "faculty",
        }
        status, data = self._request("POST", "/api/v1/users/", json_data=payload)
        self.assertEqual(status, 403, f"Expected 403 Forbidden for faculty, got: {status}")

    def test_04_hod_user_creation_is_blocked(self):
        """Verify HOD token cannot create user accounts (HTTP 403 Forbidden)."""
        self.active_user = self.user_hod
        payload = {
            "email": "hod.created@institution.edu",
            "password": "Password123!",
            "role": "student",
        }
        status, data = self._request("POST", "/api/v1/users/", json_data=payload)
        self.assertEqual(status, 403, f"Expected 403 Forbidden for HOD, got: {status}")

    def test_05_admin_user_creation_succeeds(self):
        """Verify Admin can provision a new user account with role faculty (HTTP 201 Created)."""
        self.active_user = self.user_admin
        payload = {
            "email": "dr.smith@institution.edu",
            "password": "SecurePassword123!",
            "role": "faculty",
        }
        status, data = self._request("POST", "/api/v1/users/", json_data=payload)
        self.assertEqual(status, 201, f"Expected 201 Created for admin, got: {status}, data: {data}")
        self.assertEqual(data["email"], "dr.smith@institution.edu")
        self.assertEqual(data["role"], "faculty")
        self.assertTrue(data["is_active"])
        self.assertIn("id", data)

        # Verify password was hashed in database
        created = self.db.query(User).filter(User.email == "dr.smith@institution.edu").first()
        self.assertIsNotNone(created)
        self.assertNotEqual(created.password_hash, "SecurePassword123!")

    def test_06_admin_can_provision_another_admin(self):
        """Verify Admin can provision another administrator account (HTTP 201 Created)."""
        self.active_user = self.user_admin
        payload = {
            "email": "co.admin@institution.edu",
            "password": "SecurePassword123!",
            "role": "admin",
        }
        status, data = self._request("POST", "/api/v1/users/", json_data=payload)
        self.assertEqual(status, 201, f"Expected 201 Created for co-admin, got: {status}")
        self.assertEqual(data["role"], "admin")

    def test_07_invalid_role_is_rejected(self):
        """Verify Pydantic schema rejects invalid roles (HTTP 422 Unprocessable Entity)."""
        self.active_user = self.user_admin
        payload = {
            "email": "invalid.role@institution.edu",
            "password": "SecurePassword123!",
            "role": "super_admin",
        }
        status, data = self._request("POST", "/api/v1/users/", json_data=payload)
        self.assertEqual(status, 422, f"Expected 422 for invalid role, got: {status}")

    def test_08_duplicate_email_rejected_with_409(self):
        """Verify duplicate email returns HTTP 409 Conflict."""
        self.active_user = self.user_admin
        payload = {
            "email": "admin@test.com",  # Already exists in setUp
            "password": "Password123!",
            "role": "student",
        }
        status, data = self._request("POST", "/api/v1/users/", json_data=payload)
        self.assertEqual(status, 409, f"Expected 409 Conflict for duplicate email, got: {status}")


    def test_09_anonymous_user_listing_is_blocked(self):
        """Verify unauthenticated user cannot list users (HTTP 401)."""
        self.active_user = None
        status, data = self._request("GET", "/api/v1/users/")
        self.assertEqual(status, 401)

    def test_10_student_user_listing_is_blocked(self):
        """Verify Student role cannot list users (HTTP 403 Forbidden)."""
        self.active_user = self.user_student
        status, data = self._request("GET", "/api/v1/users/")
        self.assertEqual(status, 403)

    def test_11_faculty_user_listing_is_blocked(self):
        """Verify Faculty role cannot list users (HTTP 403 Forbidden)."""
        self.active_user = self.user_faculty
        status, data = self._request("GET", "/api/v1/users/")
        self.assertEqual(status, 403)

    def test_12_hod_user_listing_is_blocked(self):
        """Verify HOD role cannot list users (HTTP 403 Forbidden)."""
        self.active_user = self.user_hod
        status, data = self._request("GET", "/api/v1/users/")
        self.assertEqual(status, 403)

    def test_13_admin_user_listing_succeeds(self):
        """Verify Admin role can list users (HTTP 200 OK) without password hashes."""
        self.active_user = self.user_admin
        status, data = self._request("GET", "/api/v1/users/")
        self.assertEqual(status, 200)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 4)
        # Check field hygiene: no password_hash exposed
        for u in data:
            self.assertIn("id", u)
            self.assertIn("email", u)
            self.assertIn("role", u)
            self.assertIn("is_active", u)
            self.assertNotIn("password_hash", u)


if __name__ == "__main__":
    unittest.main()
