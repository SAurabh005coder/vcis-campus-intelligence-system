"""
VCIS 3.0 — HOD Department Resolution Helper & Dependency Tests

Verifies that:
1. HOD with valid Faculty profile + department_id resolves the correct department.
2. HOD without Faculty profile receives 403 Forbidden.
3. HOD with Faculty profile but department_id=None receives 403 Forbidden.
4. HOD cannot accidentally resolve another user's Faculty department.
5. Faculty user is not treated as HOD by this helper -> 403 Forbidden.
6. Admin user is not treated as HOD by this helper -> 403 Forbidden.
7. Student user is not treated as HOD by this helper -> 403 Forbidden.
8. Existing authentication/authorization behavior remains unchanged.
9. FastAPI dependency get_current_hod_department enforces these rules end-to-end.
"""

import asyncio
import json
import os
import sys
import unittest

sys.path.insert(0, "backend")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["JWT_SECRET_KEY"] = "test-security-secret-key-12345-extra-secure-key"

from app.base import Base
from app.core.authorization import (
    get_current_hod_department,
    require_roles,
    resolve_hod_department_id,
)
from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.database import get_db
from app.main import app
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.user import User, UserRole

# Temporary test router to verify dependency injection end-to-end
test_router = APIRouter(prefix="/api/v1/test-hod-scope", tags=["TestHodScope"])


@test_router.get("/my-department")
def get_my_department(
    dept_id: int = Depends(get_current_hod_department),
):
    return {"department_id": dept_id}


# Include test router in app
app.include_router(test_router)


class TestHodDepartmentResolution(unittest.TestCase):
    """Test suite verifying the centralized HOD department resolution helper."""

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

        # Seed Department fixtures
        self.dept_cs = Department(
            id=1,
            name="Computer Science and Engineering",
            code="CSE",
            is_active=True,
        )
        self.dept_ec = Department(
            id=2,
            name="Electronics and Communication",
            code="ECE",
            is_active=True,
        )
        self.db.add_all([self.dept_cs, self.dept_ec])

        # Seed User fixtures
        self.user_admin = User(
            id=1,
            email="admin@test.com",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.user_hod_cs = User(
            id=2,
            email="hod.cs@test.com",
            password_hash=hash_password("hodpass123"),
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_hod_unassigned = User(
            id=3,
            email="hod.unassigned@test.com",
            password_hash=hash_password("hodpass123"),
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_faculty = User(
            id=4,
            email="faculty@test.com",
            password_hash=hash_password("facpass123"),
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_student = User(
            id=5,
            email="student@test.com",
            password_hash=hash_password("stupass123"),
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add_all([
            self.user_admin,
            self.user_hod_cs,
            self.user_hod_unassigned,
            self.user_faculty,
            self.user_student,
        ])
        self.db.commit()

        # Associate Faculty record for user_hod_cs -> dept_cs (id=1)
        self.faculty_hod = Faculty(
            id=1,
            user_id=self.user_hod_cs.id,
            department_id=self.dept_cs.id,
            employee_code="HOD-CSE-001",
            first_name="Grace",
            last_name="Hopper",
            designation="Head of Department",
            is_active=True,
        )
        # Associate Faculty record for user_faculty -> dept_ec (id=2)
        self.faculty_member = Faculty(
            id=2,
            user_id=self.user_faculty.id,
            department_id=self.dept_ec.id,
            employee_code="FAC-ECE-001",
            first_name="Alan",
            last_name="Turing",
            designation="Professor",
            is_active=True,
        )
        self.db.add_all([self.faculty_hod, self.faculty_member])
        self.db.commit()

        self.active_user = None
        app.dependency_overrides[get_db] = lambda: self.db

        def override_current_user():
            if self.active_user is None:
                raise HTTPException(
                    status_code=401,
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
            "http_version": "1.1",
            "method": method.upper(),
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": b"",
            "headers": headers,
        }

        async def receive():
            return {"type": "http.request", "body": body}

        asyncio.run(app(scope, receive, send))

        raw_content = b"".join(response_body).decode("utf-8")
        try:
            parsed = json.loads(raw_content) if raw_content else {}
        except Exception:
            parsed = {"raw": raw_content}

        return status_code[0], parsed

    # -------------------------------------------------------------------------
    # Unit Tests for resolve_hod_department_id
    # -------------------------------------------------------------------------

    def test_01_hod_with_valid_faculty_profile_resolves_department(self):
        """1. HOD with valid Faculty profile + department_id resolves the correct department."""
        dept_id = resolve_hod_department_id(self.user_hod_cs, self.db)
        self.assertEqual(dept_id, self.dept_cs.id)

    def test_02_hod_without_faculty_profile_receives_403(self):
        """2. HOD without Faculty profile receives 403 Forbidden."""
        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_hod_unassigned, self.db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("faculty profile", ctx.exception.detail.lower())

    def test_03_hod_with_faculty_profile_null_department_receives_403(self):
        """3. HOD with Faculty profile but department_id=None receives 403 Forbidden."""
        from unittest.mock import MagicMock

        # Create a Faculty object where department_id is None
        mock_faculty = Faculty(
            id=99,
            user_id=self.user_hod_unassigned.id,
            department_id=1,  # initial dummy to satisfy constructor
            employee_code="HOD-NULL-001",
            first_name="Test",
            last_name="Null",
            designation="Head of Department",
        )
        # Explicitly set department_id to None
        mock_faculty.department_id = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_faculty

        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_hod_unassigned, mock_db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("assigned department", ctx.exception.detail.lower())

    def test_04_hod_cannot_resolve_another_users_faculty_department(self):
        """4. HOD cannot accidentally resolve another user's Faculty department."""
        # user_hod_unassigned (id=3) has no faculty record.
        # user_hod_cs (id=2) has faculty record with dept_cs (id=1).
        # user_faculty (id=4) has faculty record with dept_ec (id=2).
        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_hod_unassigned, self.db)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_05_faculty_user_is_not_treated_as_hod(self):
        """5. Faculty user is not treated as HOD by this helper -> 403 Forbidden."""
        # user_faculty HAS a valid Faculty profile and department_id=2, but role=FACULTY
        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_faculty, self.db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("not authorized as a head of department", ctx.exception.detail.lower())

    def test_06_admin_user_is_not_treated_as_hod(self):
        """6. Admin user is not treated as HOD by this helper -> 403 Forbidden."""
        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_admin, self.db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("not authorized as a head of department", ctx.exception.detail.lower())

    def test_07_student_user_is_not_treated_as_hod(self):
        """7. Student user is not treated as HOD by this helper -> 403 Forbidden."""
        with self.assertRaises(HTTPException) as ctx:
            resolve_hod_department_id(self.user_student, self.db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("not authorized as a head of department", ctx.exception.detail.lower())

    def test_08_existing_authentication_authorization_behavior_unchanged(self):
        """8. Existing authentication/authorization behavior (require_roles) remains unchanged."""
        # require_roles for ADMIN
        admin_guard = require_roles(UserRole.ADMIN)
        res_admin = admin_guard(current_user=self.user_admin)
        self.assertEqual(res_admin.id, self.user_admin.id)

        # Non-admin fails require_roles(UserRole.ADMIN) with 403
        with self.assertRaises(HTTPException) as ctx:
            admin_guard(current_user=self.user_hod_cs)
        self.assertEqual(ctx.exception.status_code, 403)

        # require_roles for HOD
        hod_guard = require_roles(UserRole.HOD)
        res_hod = hod_guard(current_user=self.user_hod_cs)
        self.assertEqual(res_hod.id, self.user_hod_cs.id)

        with self.assertRaises(HTTPException) as ctx:
            hod_guard(current_user=self.user_student)
        self.assertEqual(ctx.exception.status_code, 403)

    # -------------------------------------------------------------------------
    # Integration Tests for get_current_hod_department Dependency
    # -------------------------------------------------------------------------

    def test_09_dependency_resolves_department_for_authenticated_hod(self):
        """FastAPI dependency successfully resolves department ID for valid HOD."""
        self.active_user = self.user_hod_cs
        status_code, data = self._request("GET", "/api/v1/test-hod-scope/my-department")
        self.assertEqual(status_code, 200)
        self.assertEqual(data["department_id"], self.dept_cs.id)

    def test_10_dependency_rejects_unassigned_hod_with_403(self):
        """FastAPI dependency rejects HOD with no faculty profile with 403 Forbidden."""
        self.active_user = self.user_hod_unassigned
        status_code, data = self._request("GET", "/api/v1/test-hod-scope/my-department")
        self.assertEqual(status_code, 403)
        self.assertIn("faculty profile", data.get("detail", "").lower())

    def test_11_dependency_rejects_faculty_user_with_403(self):
        """FastAPI dependency rejects Faculty caller with 403 Forbidden."""
        self.active_user = self.user_faculty
        status_code, data = self._request("GET", "/api/v1/test-hod-scope/my-department")
        self.assertEqual(status_code, 403)
        self.assertIn("not authorized as a head of department", data.get("detail", "").lower())

    def test_12_dependency_rejects_student_user_with_403(self):
        """FastAPI dependency rejects Student caller with 403 Forbidden."""
        self.active_user = self.user_student
        status_code, data = self._request("GET", "/api/v1/test-hod-scope/my-department")
        self.assertEqual(status_code, 403)
        self.assertIn("not authorized as a head of department", data.get("detail", "").lower())

    def test_13_dependency_rejects_admin_user_with_403(self):
        """FastAPI dependency rejects Admin caller with 403 Forbidden."""
        self.active_user = self.user_admin
        status_code, data = self._request("GET", "/api/v1/test-hod-scope/my-department")
        self.assertEqual(status_code, 403)
        self.assertIn("not authorized as a head of department", data.get("detail", "").lower())

    def test_14_dependency_rejects_unauthenticated_user_with_401(self):
        """FastAPI dependency rejects unauthenticated caller with 401 Unauthorized."""
        self.active_user = None
        status_code, data = self._request(
            "GET",
            "/api/v1/test-hod-scope/my-department",
            include_auth=False,
        )
        self.assertEqual(status_code, 401)


if __name__ == "__main__":
    unittest.main()
