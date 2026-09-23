"""
VCIS 3.0 — HOD Faculty Profile & Department Association Prerequisite Tests

Verifies that:
1. ADMIN creates Faculty profile for FACULTY user -> 201 Created.
2. ADMIN creates Faculty profile for HOD user -> 201 Created.
3. Created HOD Faculty profile has correct user_id.
4. Created HOD Faculty profile has correct department_id.
5. STUDENT cannot create Faculty profile -> 403 Forbidden.
6. FACULTY cannot create Faculty profile -> 403 Forbidden.
7. HOD cannot create Faculty profile -> 403 Forbidden.
8. ADMIN cannot create Faculty profile for STUDENT -> 400 Bad Request.
9. ADMIN cannot create Faculty profile for ADMIN -> 400 Bad Request.
10. Duplicate HOD Faculty profile is rejected using existing protection -> 409 Conflict.
11. Existing ordinary Faculty provisioning continues passing.
12. Existing HOD authentication/login continues passing.
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

os.environ["JWT_SECRET_KEY"] = "test-security-secret-key-12345-extra-secure-key"

from app.base import Base
from app.core.authorization import resolve_hod_department_id
from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.database import get_db
from app.main import app
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.user import User, UserRole


class TestHodFacultyProfilePrerequisite(unittest.TestCase):
    """Test suite verifying HOD faculty profile provisioning."""

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
        self.user_hod = User(
            id=2,
            email="hod.cse@test.com",
            password_hash=hash_password("hodpass123"),
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_faculty = User(
            id=3,
            email="faculty1@test.com",
            password_hash=hash_password("facpass123"),
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_student = User(
            id=4,
            email="student1@test.com",
            password_hash=hash_password("stupass123"),
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

    def test_01_admin_creates_faculty_profile_for_faculty_user_succeeds(self):
        """ADMIN creates Faculty profile for FACULTY user -> 201."""
        self.active_user = self.user_admin
        payload = {
            "user_id": self.user_faculty.id,
            "department_id": self.dept_cs.id,
            "employee_code": "FAC-CSE-001",
            "first_name": "Alan",
            "last_name": "Turing",
            "designation": "Associate Professor",
            "phone": "+1-555-0101",
        }
        status_code, data = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 201)
        self.assertEqual(data["user_id"], self.user_faculty.id)
        self.assertEqual(data["department_id"], self.dept_cs.id)
        self.assertEqual(data["employee_code"], "FAC-CSE-001")

    def test_02_admin_creates_faculty_profile_for_hod_user_succeeds(self):
        """ADMIN creates Faculty profile for HOD user -> 201."""
        self.active_user = self.user_admin
        payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-001",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
            "phone": "+1-555-0102",
        }
        status_code, data = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 201)
        self.assertEqual(data["employee_code"], "HOD-CSE-001")

    def test_03_created_hod_faculty_profile_has_correct_user_id(self):
        """Created HOD Faculty profile has correct user_id."""
        self.active_user = self.user_admin
        payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-002",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, data = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 201)
        self.assertEqual(data["user_id"], self.user_hod.id)

        # Confirm persisted in DB
        faculty_record = self.db.query(Faculty).filter(Faculty.user_id == self.user_hod.id).first()
        self.assertIsNotNone(faculty_record)
        self.assertEqual(faculty_record.user_id, self.user_hod.id)

    def test_04_created_hod_faculty_profile_has_correct_department_id(self):
        """Created HOD Faculty profile has correct department_id."""
        self.active_user = self.user_admin
        payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_ec.id,
            "employee_code": "HOD-ECE-001",
            "first_name": "Claude",
            "last_name": "Shannon",
            "designation": "Head of Department",
        }
        status_code, data = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 201)
        self.assertEqual(data["department_id"], self.dept_ec.id)

        # Confirm persisted in DB
        faculty_record = self.db.query(Faculty).filter(Faculty.user_id == self.user_hod.id).first()
        self.assertIsNotNone(faculty_record)
        self.assertEqual(faculty_record.department_id, self.dept_ec.id)

    def test_05_student_cannot_create_faculty_profile(self):
        """STUDENT cannot create Faculty profile -> 403."""
        self.active_user = self.user_student
        payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-003",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, _ = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 403)

    def test_06_faculty_cannot_create_faculty_profile(self):
        """FACULTY cannot create Faculty profile -> 403."""
        self.active_user = self.user_faculty
        payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-004",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, _ = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 403)

    def test_07_hod_cannot_create_faculty_profile(self):
        """HOD cannot create Faculty profile (cannot provision self) -> 403."""
        self.active_user = self.user_hod
        payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-005",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, _ = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 403)

    def test_08_admin_cannot_create_faculty_profile_for_student(self):
        """ADMIN cannot create Faculty profile for STUDENT -> 400 Bad Request."""
        self.active_user = self.user_admin
        payload = {
            "user_id": self.user_student.id,
            "department_id": self.dept_cs.id,
            "employee_code": "STU-FAC-001",
            "first_name": "Student",
            "last_name": "One",
            "designation": "Instructor",
        }
        status_code, data = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 400)
        self.assertIn("eligible role", data.get("detail", "").lower())

    def test_09_admin_cannot_create_faculty_profile_for_admin(self):
        """ADMIN cannot create Faculty profile for ADMIN -> 400 Bad Request."""
        self.active_user = self.user_admin
        payload = {
            "user_id": self.user_admin.id,
            "department_id": self.dept_cs.id,
            "employee_code": "ADM-FAC-001",
            "first_name": "Admin",
            "last_name": "User",
            "designation": "Professor",
        }
        status_code, data = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 400)
        self.assertIn("eligible role", data.get("detail", "").lower())

    def test_10_duplicate_hod_faculty_profile_rejected(self):
        """Duplicate HOD Faculty profile is rejected using existing protection -> 409 Conflict."""
        self.active_user = self.user_admin
        payload1 = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-100",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code1, _ = self._request("POST", "/api/v1/faculty/", json_data=payload1)
        self.assertEqual(status_code1, 201)

        # Attempt to create another faculty profile for the same HOD
        payload2 = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_ec.id,
            "employee_code": "HOD-CSE-101",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code2, data2 = self._request("POST", "/api/v1/faculty/", json_data=payload2)
        self.assertEqual(status_code2, 409)
        self.assertIn("already has a faculty profile", data2.get("detail", "").lower())

    def test_11_existing_ordinary_faculty_provisioning_passes(self):
        """Existing ordinary Faculty provisioning continues passing."""
        self.active_user = self.user_admin
        # Create second faculty user
        fac_user_2 = User(
            id=5,
            email="faculty2@test.com",
            password_hash=hash_password("facpass2"),
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.db.add(fac_user_2)
        self.db.commit()

        payload = {
            "user_id": fac_user_2.id,
            "department_id": self.dept_ec.id,
            "employee_code": "FAC-ECE-002",
            "first_name": "Ada",
            "last_name": "Lovelace",
            "designation": "Assistant Professor",
        }
        status_code, data = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 201)
        self.assertEqual(data["employee_code"], "FAC-ECE-002")
        self.assertEqual(data["user_id"], fac_user_2.id)
        self.assertEqual(data["department_id"], self.dept_ec.id)

    def test_12_existing_hod_authentication_login_continues_passing(self):
        """Existing HOD authentication/login continues passing."""
        # Provision HOD faculty profile
        self.active_user = self.user_admin
        payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-AUTH",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, _ = self._request("POST", "/api/v1/faculty/", json_data=payload)
        self.assertEqual(status_code, 201)

        # 1. Test unauthenticated POST to /api/v1/auth/login with HOD credentials
        login_payload = {
            "email": self.user_hod.email,
            "password": "hodpass123",
        }
        status_code_login, data_login = self._request(
            "POST",
            "/api/v1/auth/login",
            json_data=login_payload,
            include_auth=False,
        )
        self.assertEqual(status_code_login, 200)
        self.assertIn("access_token", data_login)
        self.assertEqual(data_login["token_type"], "bearer")

        # 2. Authenticate via /api/v1/users/me using active_user = HOD
        self.active_user = self.user_hod
        status_code_me, data_me = self._request("GET", "/api/v1/users/me")
        self.assertEqual(status_code_me, 200)
        self.assertEqual(data_me["email"], self.user_hod.email)
        self.assertEqual(data_me["role"], UserRole.HOD.value)

    def test_13_admin_updates_hod_department_succeeds(self):
        """ADMIN updates HOD department -> 200 OK, DB and resolver reflect new department."""
        # Provision HOD faculty profile in dept_cs
        self.active_user = self.user_admin
        create_payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-UPD",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
            "phone": "+1-555-0199",
        }
        status_code, created_data = self._request("POST", "/api/v1/faculty/", json_data=create_payload)
        self.assertEqual(status_code, 201)
        faculty_id = created_data["id"]

        # Admin updates HOD department to dept_ec
        update_payload = {
            "department_id": self.dept_ec.id,
            "employee_code": "HOD-CSE-UPD",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
            "phone": "+1-555-0199",
            "is_active": True,
        }
        status_code_put, update_data = self._request("PUT", f"/api/v1/faculty/{faculty_id}", json_data=update_payload)
        self.assertEqual(status_code_put, 200)
        self.assertEqual(update_data["department_id"], self.dept_ec.id)

        # Confirm persisted in DB
        self.db.expire_all()
        persisted = self.db.query(Faculty).filter(Faculty.id == faculty_id).first()
        self.assertEqual(persisted.department_id, self.dept_ec.id)

        # Confirm server-side HOD resolver reflects newly assigned department
        resolved_dept_id = resolve_hod_department_id(self.user_hod, self.db)
        self.assertEqual(resolved_dept_id, self.dept_ec.id)

    def test_14_hod_cannot_update_own_department(self):
        """HOD cannot update their own department -> 403 Forbidden."""
        self.active_user = self.user_admin
        create_payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-RBAC",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, created_data = self._request("POST", "/api/v1/faculty/", json_data=create_payload)
        self.assertEqual(status_code, 201)
        faculty_id = created_data["id"]

        # HOD attempts to change their own department to dept_ec
        self.active_user = self.user_hod
        update_payload = {
            "department_id": self.dept_ec.id,
            "employee_code": "HOD-CSE-RBAC",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
            "is_active": True,
        }
        status_code_put, _ = self._request("PUT", f"/api/v1/faculty/{faculty_id}", json_data=update_payload)
        self.assertEqual(status_code_put, 403)

        # Confirm department was NOT changed in DB
        self.db.expire_all()
        persisted = self.db.query(Faculty).filter(Faculty.id == faculty_id).first()
        self.assertEqual(persisted.department_id, self.dept_cs.id)

    def test_15_faculty_cannot_update_hod_department(self):
        """FACULTY cannot update an HOD department -> 403 Forbidden."""
        self.active_user = self.user_admin
        create_payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-FAC",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, created_data = self._request("POST", "/api/v1/faculty/", json_data=create_payload)
        self.assertEqual(status_code, 201)
        faculty_id = created_data["id"]

        self.active_user = self.user_faculty
        update_payload = {
            "department_id": self.dept_ec.id,
            "employee_code": "HOD-CSE-FAC",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
            "is_active": True,
        }
        status_code_put, _ = self._request("PUT", f"/api/v1/faculty/{faculty_id}", json_data=update_payload)
        self.assertEqual(status_code_put, 403)

    def test_16_student_cannot_update_hod_department(self):
        """STUDENT cannot update an HOD department -> 403 Forbidden."""
        self.active_user = self.user_admin
        create_payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-STU",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, created_data = self._request("POST", "/api/v1/faculty/", json_data=create_payload)
        self.assertEqual(status_code, 201)
        faculty_id = created_data["id"]

        self.active_user = self.user_student
        update_payload = {
            "department_id": self.dept_ec.id,
            "employee_code": "HOD-CSE-STU",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
            "is_active": True,
        }
        status_code_put, _ = self._request("PUT", f"/api/v1/faculty/{faculty_id}", json_data=update_payload)
        self.assertEqual(status_code_put, 403)

    def test_17_admin_update_hod_invalid_department_rejected(self):
        """ADMIN updating HOD with nonexistent department ID -> 404 Not Found."""
        self.active_user = self.user_admin
        create_payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-INV",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, created_data = self._request("POST", "/api/v1/faculty/", json_data=create_payload)
        self.assertEqual(status_code, 201)
        faculty_id = created_data["id"]

        update_payload = {
            "department_id": 99999,
            "employee_code": "HOD-CSE-INV",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
            "is_active": True,
        }
        status_code_put, data = self._request("PUT", f"/api/v1/faculty/{faculty_id}", json_data=update_payload)
        self.assertEqual(status_code_put, 404)
        self.assertIn("active department", data.get("detail", "").lower())

    def test_18_admin_update_hod_inactive_department_rejected(self):
        """ADMIN updating HOD with inactive department ID -> 404 Not Found."""
        self.active_user = self.user_admin
        # Create an inactive department
        inactive_dept = Department(
            id=99,
            name="Inactive Department",
            code="INACT",
            is_active=False,
        )
        self.db.add(inactive_dept)
        self.db.commit()

        create_payload = {
            "user_id": self.user_hod.id,
            "department_id": self.dept_cs.id,
            "employee_code": "HOD-CSE-INACT",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
        }
        status_code, created_data = self._request("POST", "/api/v1/faculty/", json_data=create_payload)
        self.assertEqual(status_code, 201)
        faculty_id = created_data["id"]

        update_payload = {
            "department_id": inactive_dept.id,
            "employee_code": "HOD-CSE-INACT",
            "first_name": "Grace",
            "last_name": "Hopper",
            "designation": "Head of Department",
            "is_active": True,
        }
        status_code_put, data = self._request("PUT", f"/api/v1/faculty/{faculty_id}", json_data=update_payload)
        self.assertEqual(status_code_put, 404)
        self.assertIn("active department", data.get("detail", "").lower())


if __name__ == "__main__":
    unittest.main()

