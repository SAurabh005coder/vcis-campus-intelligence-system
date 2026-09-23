"""
VCIS 3.0 — Academic Governance & HOD Course/Subject Proposal Workflow Test Suite
Comprehensive testing verifying 32 required governance, authorization, IDOR, and transactional scenarios.
"""

import asyncio
from datetime import datetime, timezone
import json
import os
import sys
import unittest

import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, "backend")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-governance-secret-key-9876543210"

from app.base import Base
from app.core.security import hash_password
from app.database import get_db
from app.main import app
from app.models.course import Course
from app.models.course_proposal import CourseProposal, ProposalStatus
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.subject import Subject
from app.models.subject_proposal import SubjectProposal
from app.models.user import User, UserRole


class TestAcademicProposals(unittest.TestCase):
    """32 mandatory tests covering academic proposals governance, RBAC, and transactions."""

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

        # Seed Departments
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

        # Seed Users
        self.user_admin = User(
            id=1,
            email="admin@vcis.lan",
            password_hash=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.user_hod_cs = User(
            id=2,
            email="hod.cs@vcis.lan",
            password_hash=hash_password("HodPass123!"),
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_hod_ec = User(
            id=3,
            email="hod.ec@vcis.lan",
            password_hash=hash_password("HodPass123!"),
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_hod_unassigned = User(
            id=4,
            email="hod.unassigned@vcis.lan",
            password_hash=hash_password("HodPass123!"),
            role=UserRole.HOD,
            is_active=True,
        )
        self.user_faculty = User(
            id=5,
            email="faculty@vcis.lan",
            password_hash=hash_password("FacultyPass123!"),
            role=UserRole.FACULTY,
            is_active=True,
        )
        self.user_student = User(
            id=6,
            email="student@vcis.lan",
            password_hash=hash_password("StudentPass123!"),
            role=UserRole.STUDENT,
            is_active=True,
        )
        self.db.add_all([
            self.user_admin,
            self.user_hod_cs,
            self.user_hod_ec,
            self.user_hod_unassigned,
            self.user_faculty,
            self.user_student,
        ])

        # Seed Faculty profiles to link HODs to Departments
        self.faculty_hod_cs = Faculty(
            id=1,
            user_id=self.user_hod_cs.id,
            department_id=self.dept_cs.id,
            employee_code="FAC-HOD-CS-01",
            first_name="Alan",
            last_name="Turing",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_hod_ec = Faculty(
            id=2,
            user_id=self.user_hod_ec.id,
            department_id=self.dept_ec.id,
            employee_code="FAC-HOD-EC-01",
            first_name="Claude",
            last_name="Shannon",
            designation="Professor & HOD",
            is_active=True,
        )
        self.faculty_regular = Faculty(
            id=3,
            user_id=self.user_faculty.id,
            department_id=self.dept_cs.id,
            employee_code="FAC-REG-01",
            first_name="Grace",
            last_name="Hopper",
            designation="Assistant Professor",
            is_active=True,
        )
        self.db.add_all([self.faculty_hod_cs, self.faculty_hod_ec, self.faculty_regular])

        # Seed Official Courses
        self.course_mca = Course(
            id=1,
            department_id=self.dept_cs.id,
            name="Master of Computer Applications",
            code="MCA",
            duration_years=2,
            total_semesters=4,
            is_active=True,
        )
        self.course_btech_ec = Course(
            id=2,
            department_id=self.dept_ec.id,
            name="B.Tech Electronics",
            code="BTECH-EC",
            duration_years=4,
            total_semesters=8,
            is_active=True,
        )
        self.db.add_all([self.course_mca, self.course_btech_ec])

        # Seed Official Subject
        self.subject_dsa = Subject(
            id=1,
            course_id=self.course_mca.id,
            name="Data Structures and Algorithms",
            code="MCA-101",
            semester=1,
            credits=4,
            is_active=True,
        )
        self.db.add(self.subject_dsa)
        self.db.commit()

        # Override get_db dependency to point to the in-memory test session
        def override_get_db():
            test_db = self.Session()
            try:
                yield test_db
            finally:
                test_db.close()

        app.dependency_overrides[get_db] = override_get_db

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()

    def _generate_token(self, user: User) -> str:
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
        return jwt.encode(payload, os.environ["JWT_SECRET_KEY"], algorithm="HS256")

    def _request(self, method: str, path: str, token: str = None, json_body: dict = None):
        headers = []
        if token:
            headers.append((b"authorization", f"Bearer {token}".encode("utf-8")))
        if json_body is not None:
            headers.append((b"content-type", b"application/json"))
            body = json.dumps(json_body).encode("utf-8")
        else:
            body = b""

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

    # =========================================================================
    # PART 1: COURSE PROPOSALS (1 - 13)
    # =========================================================================

    def test_01_hod_can_create_course_proposal_for_own_department(self):
        """1. HOD can create proposal for own department."""
        token = self._generate_token(self.user_hod_cs)
        status, data = self._request("POST", "/api/v1/course-proposals/", token, {
            "name": "M.Tech Artificial Intelligence",
            "code": "MTECH-AI",
            "description": "Advanced AI curriculum",
            "duration_years": 2,
            "total_semesters": 4,
        })
        self.assertEqual(status, 201)
        self.assertEqual(data["status"], "PENDING_APPROVAL")
        self.assertEqual(data["department_id"], self.dept_cs.id)
        self.assertEqual(data["proposed_by"], self.user_hod_cs.id)

    def test_02_hod_cannot_specify_another_department_in_payload(self):
        """2. HOD cannot specify another department (payload value is ignored/overridden)."""
        token = self._generate_token(self.user_hod_cs)
        # Attempt to inject department_id = 2 (ECE)
        status, data = self._request("POST", "/api/v1/course-proposals/", token, {
            "name": "M.Tech Robotics",
            "code": "MTECH-ROB",
            "duration_years": 2,
            "total_semesters": 4,
            "department_id": self.dept_ec.id,
        })
        self.assertEqual(status, 201)
        # Verified: assigned to HOD's actual department (CSE = 1), not injected ECE = 2
        self.assertEqual(data["department_id"], self.dept_cs.id)

    def test_03_hod_without_department_cannot_create_proposal(self):
        """3. HOD without department assignment cannot create proposal -> 403."""
        token = self._generate_token(self.user_hod_unassigned)
        status, data = self._request("POST", "/api/v1/course-proposals/", token, {
            "name": "M.Tech Data Science",
            "code": "MTECH-DS",
            "duration_years": 2,
            "total_semesters": 4,
        })
        self.assertEqual(status, 403)

    def test_04_faculty_cannot_create_course_proposal(self):
        """4. Faculty cannot create course proposal -> 403."""
        token = self._generate_token(self.user_faculty)
        status, data = self._request("POST", "/api/v1/course-proposals/", token, {
            "name": "M.Tech Cybersecurity",
            "code": "MTECH-CYBER",
            "duration_years": 2,
            "total_semesters": 4,
        })
        self.assertEqual(status, 403)

    def test_05_student_cannot_create_course_proposal(self):
        """5. Student cannot create course proposal -> 403."""
        token = self._generate_token(self.user_student)
        status, data = self._request("POST", "/api/v1/course-proposals/", token, {
            "name": "M.Tech Cloud",
            "code": "MTECH-CLOUD",
            "duration_years": 2,
            "total_semesters": 4,
        })
        self.assertEqual(status, 403)

    def test_06_admin_can_view_proposals_and_cannot_create(self):
        """6. Admin can view all proposals, but cannot create proposals via HOD endpoint."""
        admin_token = self._generate_token(self.user_admin)
        # Admin cannot create (HOD-only)
        status_create, _ = self._request("POST", "/api/v1/course-proposals/", admin_token, {
            "name": "Admin Course",
            "code": "ADM-CRS",
            "duration_years": 2,
            "total_semesters": 4,
        })
        self.assertEqual(status_create, 403)

        # Admin can view all proposals
        status_list, list_data = self._request("GET", "/api/v1/course-proposals/", admin_token)
        self.assertEqual(status_list, 200)
        self.assertIsInstance(list_data, list)

    def test_07_admin_can_approve_proposal(self):
        """7. Admin can approve a pending course proposal."""
        # Create proposal first
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "B.Tech Computer Science",
            "code": "BTECH-CS",
            "duration_years": 4,
            "total_semesters": 8,
        })

        admin_token = self._generate_token(self.user_admin)
        status, data = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/approve", admin_token, {
            "review_comment": "Curriculum standards met. Approved.",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "APPROVED")
        self.assertEqual(data["reviewed_by"], self.user_admin.id)
        self.assertIsNotNone(data["reviewed_at"])

    def test_08_admin_can_reject_proposal(self):
        """8. Admin can reject a proposal with mandatory reason."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "Diploma CS",
            "code": "DIP-CS",
            "duration_years": 1,
            "total_semesters": 2,
        })

        admin_token = self._generate_token(self.user_admin)
        status, data = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/reject", admin_token, {
            "review_comment": "Diploma programs not currently supported.",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "REJECTED")
        self.assertEqual(data["review_comment"], "Diploma programs not currently supported.")

    def test_08b_course_proposal_rejection_whitespace_comment_returns_422(self):
        """8b. Course proposal rejection with whitespace-only comment returns HTTP 422 and retains PENDING_APPROVAL."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "Diploma CS Whitespace",
            "code": "DIP-WS",
            "duration_years": 1,
            "total_semesters": 2,
        })

        admin_token = self._generate_token(self.user_admin)
        status, data = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/reject", admin_token, {
            "review_comment": "   ",
        })
        self.assertEqual(status, 422)

        # Verify proposal status was not modified
        refreshed_prop = self.db.query(CourseProposal).filter(CourseProposal.id == prop["id"]).first()
        self.assertEqual(refreshed_prop.status, ProposalStatus.PENDING_APPROVAL)

    def test_09_approved_proposal_creates_exactly_one_official_course(self):
        """9. Approved proposal creates exactly one official course."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "M.Tech Software Engineering",
            "code": "MTECH-SE",
            "duration_years": 2,
            "total_semesters": 4,
        })

        admin_token = self._generate_token(self.user_admin)
        self._request("POST", f"/api/v1/course-proposals/{prop['id']}/approve", admin_token)

        # Verify exactly one official course was created
        created_course = self.db.query(Course).filter(Course.code == "MTECH-SE").all()
        self.assertEqual(len(created_course), 1)
        self.assertEqual(created_course[0].name, "M.Tech Software Engineering")
        self.assertEqual(created_course[0].department_id, self.dept_cs.id)

    def test_10_rejected_proposal_does_not_create_course(self):
        """10. Rejected proposal does not create an official course."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "B.Sc Computing",
            "code": "BSC-COMP",
            "duration_years": 3,
            "total_semesters": 6,
        })

        admin_token = self._generate_token(self.user_admin)
        self._request("POST", f"/api/v1/course-proposals/{prop['id']}/reject", admin_token, {
            "review_comment": "Degree not authorized.",
        })

        official_count = self.db.query(Course).filter(Course.code == "BSC-COMP").count()
        self.assertEqual(official_count, 0)

    def test_11_already_approved_proposal_cannot_be_approved_again(self):
        """11. Already approved proposal cannot be approved again -> 400."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "Course Once",
            "code": "CRS-ONCE",
            "duration_years": 2,
            "total_semesters": 4,
        })
        admin_token = self._generate_token(self.user_admin)
        self._request("POST", f"/api/v1/course-proposals/{prop['id']}/approve", admin_token)

        # Second approval attempt
        status, data = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/approve", admin_token)
        self.assertEqual(status, 400)

    def test_12_already_rejected_proposal_cannot_be_rejected_or_approved_again(self):
        """12. Already rejected proposal cannot be approved or rejected again -> 400."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "Course Reject Once",
            "code": "CRS-REJ-ONCE",
            "duration_years": 2,
            "total_semesters": 4,
        })
        admin_token = self._generate_token(self.user_admin)
        self._request("POST", f"/api/v1/course-proposals/{prop['id']}/reject", admin_token, {
            "review_comment": "Initial rejection.",
        })

        # Attempt to reject again
        status_rej, _ = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/reject", admin_token, {
            "review_comment": "Second rejection attempt.",
        })
        self.assertEqual(status_rej, 400)

        # Attempt to approve rejected proposal
        status_app, _ = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/approve", admin_token)
        self.assertEqual(status_app, 400)

    def test_13_duplicate_course_code_or_name_rejected_safely(self):
        """13. Duplicate course code/name rejected safely -> 409 Conflict."""
        hod_token = self._generate_token(self.user_hod_cs)
        # Attempt to propose already existing official course code "MCA"
        status, data = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "Duplicate Master of Computer Applications",
            "code": "MCA",
            "duration_years": 2,
            "total_semesters": 4,
        })
        self.assertEqual(status, 409)

    # =========================================================================
    # PART 2: SUBJECT PROPOSALS (14 - 23)
    # =========================================================================

    def test_14_hod_can_create_subject_proposal_for_own_dept_course(self):
        """14. HOD can create subject proposal for own department course."""
        token = self._generate_token(self.user_hod_cs)
        status, data = self._request("POST", "/api/v1/subject-proposals/", token, {
            "course_id": self.course_mca.id,
            "name": "Advanced Operating Systems",
            "code": "MCA-102",
            "semester": 1,
            "credits": 4,
        })
        self.assertEqual(status, 201)
        self.assertEqual(data["status"], "PENDING_APPROVAL")
        self.assertEqual(data["course_id"], self.course_mca.id)

    def test_15_hod_cannot_create_subject_proposal_for_another_dept_course(self):
        """15. HOD cannot create subject proposal for another department's course -> 403."""
        token = self._generate_token(self.user_hod_cs)
        # Attempt to propose subject for BTECH-EC which belongs to ECE dept
        status, data = self._request("POST", "/api/v1/subject-proposals/", token, {
            "course_id": self.course_btech_ec.id,
            "name": "Digital Signal Processing",
            "code": "ECE-301",
            "semester": 3,
            "credits": 4,
        })
        self.assertEqual(status, 403)

    def test_16_faculty_cannot_create_subject_proposal(self):
        """16. Faculty cannot create subject proposal -> 403."""
        token = self._generate_token(self.user_faculty)
        status, data = self._request("POST", "/api/v1/subject-proposals/", token, {
            "course_id": self.course_mca.id,
            "name": "Faculty Subject",
            "code": "MCA-FAC",
            "semester": 1,
            "credits": 3,
        })
        self.assertEqual(status, 403)

    def test_17_student_cannot_create_subject_proposal(self):
        """17. Student cannot create subject proposal -> 403."""
        token = self._generate_token(self.user_student)
        status, data = self._request("POST", "/api/v1/subject-proposals/", token, {
            "course_id": self.course_mca.id,
            "name": "Student Subject",
            "code": "MCA-STUD",
            "semester": 1,
            "credits": 3,
        })
        self.assertEqual(status, 403)

    def test_18_admin_can_approve_subject_proposal(self):
        """18. Admin can approve a pending subject proposal."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/subject-proposals/", hod_token, {
            "course_id": self.course_mca.id,
            "name": "Cloud Architecture",
            "code": "MCA-201",
            "semester": 2,
            "credits": 4,
        })

        admin_token = self._generate_token(self.user_admin)
        status, data = self._request("POST", f"/api/v1/subject-proposals/{prop['id']}/approve", admin_token, {
            "review_comment": "Approved for Semester 2.",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "APPROVED")

    def test_19_admin_can_reject_subject_proposal(self):
        """19. Admin can reject subject proposal with reason."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/subject-proposals/", hod_token, {
            "course_id": self.course_mca.id,
            "name": "Intro to Basic Programming",
            "code": "MCA-BASIC",
            "semester": 1,
            "credits": 2,
        })

        admin_token = self._generate_token(self.user_admin)
        status, data = self._request("POST", f"/api/v1/subject-proposals/{prop['id']}/reject", admin_token, {
            "review_comment": "Curriculum overlap with prerequisite course.",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "REJECTED")
        self.assertEqual(data["review_comment"], "Curriculum overlap with prerequisite course.")

    def test_19b_subject_proposal_rejection_whitespace_comment_returns_422(self):
        """19b. Subject proposal rejection with whitespace-only comment returns HTTP 422 and retains PENDING_APPROVAL."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/subject-proposals/", hod_token, {
            "course_id": self.course_mca.id,
            "name": "Basic Programming Whitespace",
            "code": "MCA-WS",
            "semester": 1,
            "credits": 2,
        })

        admin_token = self._generate_token(self.user_admin)
        status, data = self._request("POST", f"/api/v1/subject-proposals/{prop['id']}/reject", admin_token, {
            "review_comment": "   ",
        })
        self.assertEqual(status, 422)

        # Verify proposal status was not modified
        refreshed_prop = self.db.query(SubjectProposal).filter(SubjectProposal.id == prop["id"]).first()
        self.assertEqual(refreshed_prop.status, ProposalStatus.PENDING_APPROVAL)

    def test_20_approved_proposal_creates_exactly_one_official_subject(self):
        """20. Approved proposal creates exactly one official subject."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/subject-proposals/", hod_token, {
            "course_id": self.course_mca.id,
            "name": "Distributed Databases",
            "code": "MCA-202",
            "semester": 2,
            "credits": 4,
        })

        admin_token = self._generate_token(self.user_admin)
        self._request("POST", f"/api/v1/subject-proposals/{prop['id']}/approve", admin_token)

        official = self.db.query(Subject).filter(Subject.code == "MCA-202").all()
        self.assertEqual(len(official), 1)
        self.assertEqual(official[0].name, "Distributed Databases")
        self.assertEqual(official[0].course_id, self.course_mca.id)

    def test_21_subject_proposal_semester_exceeding_course_semesters_rejected(self):
        """21. Proposed semester greater than course.total_semesters is rejected -> 400."""
        token = self._generate_token(self.user_hod_cs)
        # MCA has 4 semesters; propose semester 5
        status, data = self._request("POST", "/api/v1/subject-proposals/", token, {
            "course_id": self.course_mca.id,
            "name": "Post-Grad Thesis",
            "code": "MCA-501",
            "semester": 5,
            "credits": 6,
        })
        self.assertEqual(status, 400)

    def test_22_duplicate_subject_rejected_safely(self):
        """22. Duplicate subject code/combination rejected safely -> 409."""
        token = self._generate_token(self.user_hod_cs)
        # MCA-101 is already official
        status, data = self._request("POST", "/api/v1/subject-proposals/", token, {
            "course_id": self.course_mca.id,
            "name": "Duplicate DSA",
            "code": "MCA-101",
            "semester": 1,
            "credits": 4,
        })
        self.assertEqual(status, 409)

    def test_23_already_processed_subject_proposal_cannot_be_processed_again(self):
        """23. Already processed subject proposal cannot be approved again -> 400."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/subject-proposals/", hod_token, {
            "course_id": self.course_mca.id,
            "name": "Machine Learning",
            "code": "MCA-301",
            "semester": 3,
            "credits": 4,
        })
        admin_token = self._generate_token(self.user_admin)
        self._request("POST", f"/api/v1/subject-proposals/{prop['id']}/approve", admin_token)

        # Re-approval attempt
        status, data = self._request("POST", f"/api/v1/subject-proposals/{prop['id']}/approve", admin_token)
        self.assertEqual(status, 400)

    # =========================================================================
    # PART 3: IDOR & CROSS-DEPARTMENT SECURITY (24 - 29)
    # =========================================================================

    def test_24_hod_a_cannot_get_hod_b_course_proposal(self):
        """24. HOD A cannot GET HOD B's course proposal -> 403."""
        # HOD EC creates a proposal
        hod_ec_token = self._generate_token(self.user_hod_ec)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_ec_token, {
            "name": "M.Tech VLSI Design",
            "code": "MTECH-VLSI",
            "duration_years": 2,
            "total_semesters": 4,
        })

        # HOD CS attempts to access HOD EC's proposal
        hod_cs_token = self._generate_token(self.user_hod_cs)
        status, data = self._request("GET", f"/api/v1/course-proposals/{prop['id']}", hod_cs_token)
        self.assertEqual(status, 403)

    def test_25_hod_a_cannot_get_hod_b_subject_proposal(self):
        """25. HOD A cannot GET HOD B's subject proposal -> 403."""
        hod_ec_token = self._generate_token(self.user_hod_ec)
        _, prop = self._request("POST", "/api/v1/subject-proposals/", hod_ec_token, {
            "course_id": self.course_btech_ec.id,
            "name": "Microcontrollers",
            "code": "ECE-401",
            "semester": 4,
            "credits": 4,
        })

        hod_cs_token = self._generate_token(self.user_hod_cs)
        status, data = self._request("GET", f"/api/v1/subject-proposals/{prop['id']}", hod_cs_token)
        self.assertEqual(status, 403)

    def test_26_hod_cannot_approve_or_reject_any_proposal(self):
        """26. HOD cannot approve or reject any proposal -> 403."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "M.Tech Software Systems",
            "code": "MTECH-SS",
            "duration_years": 2,
            "total_semesters": 4,
        })

        status_app, _ = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/approve", hod_token)
        self.assertEqual(status_app, 403)

        status_rej, _ = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/reject", hod_token, {
            "review_comment": "Unauthorized self-rejection",
        })
        self.assertEqual(status_rej, 403)

    def test_27_hod_cannot_manipulate_department_id_through_payload(self):
        """27. HOD cannot manipulate department_id through payload."""
        hod_token = self._generate_token(self.user_hod_cs)
        status, data = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "Injected Dept Course",
            "code": "INJ-DEPT",
            "duration_years": 2,
            "total_semesters": 4,
            "department_id": 9999,
        })
        self.assertEqual(status, 201)
        self.assertEqual(data["department_id"], self.dept_cs.id)

    def test_28_hod_cannot_access_another_departments_course_proposals_in_list(self):
        """28. HOD cannot access another department's course proposals in list endpoint."""
        hod_cs_token = self._generate_token(self.user_hod_cs)
        hod_ec_token = self._generate_token(self.user_hod_ec)

        self._request("POST", "/api/v1/course-proposals/", hod_cs_token, {
            "name": "CS Exclusive",
            "code": "CS-EXCL",
            "duration_years": 2,
            "total_semesters": 4,
        })
        self._request("POST", "/api/v1/course-proposals/", hod_ec_token, {
            "name": "EC Exclusive",
            "code": "EC-EXCL",
            "duration_years": 2,
            "total_semesters": 4,
        })

        # HOD CS list should contain only CS
        status_cs, data_cs = self._request("GET", "/api/v1/course-proposals/", hod_cs_token)
        self.assertEqual(status_cs, 200)
        codes_cs = [p["code"] for p in data_cs]
        self.assertIn("CS-EXCL", codes_cs)
        self.assertNotIn("EC-EXCL", codes_cs)

        # HOD EC list should contain only EC
        status_ec, data_ec = self._request("GET", "/api/v1/course-proposals/", hod_ec_token)
        self.assertEqual(status_ec, 200)
        codes_ec = [p["code"] for p in data_ec]
        self.assertIn("EC-EXCL", codes_ec)
        self.assertNotIn("CS-EXCL", codes_ec)

    def test_29_hod_cannot_access_another_departments_subject_proposals_in_list(self):
        """29. HOD cannot access another department's subject proposals in list endpoint."""
        hod_cs_token = self._generate_token(self.user_hod_cs)
        hod_ec_token = self._generate_token(self.user_hod_ec)

        self._request("POST", "/api/v1/subject-proposals/", hod_cs_token, {
            "course_id": self.course_mca.id,
            "name": "CS Subj Exclusive",
            "code": "CS-SUB-EXCL",
            "semester": 1,
            "credits": 4,
        })
        self._request("POST", "/api/v1/subject-proposals/", hod_ec_token, {
            "course_id": self.course_btech_ec.id,
            "name": "EC Subj Exclusive",
            "code": "EC-SUB-EXCL",
            "semester": 1,
            "credits": 4,
        })

        status_cs, data_cs = self._request("GET", "/api/v1/subject-proposals/", hod_cs_token)
        self.assertEqual(status_cs, 200)
        codes_cs = [p["code"] for p in data_cs]
        self.assertIn("CS-SUB-EXCL", codes_cs)
        self.assertNotIn("EC-SUB-EXCL", codes_cs)

    # =========================================================================
    # PART 4: TRANSACTION & ATOMICITY TESTS (30 - 32)
    # =========================================================================

    def test_30_failed_course_creation_does_not_mark_proposal_approved(self):
        """30. Failed course creation must not mark proposal APPROVED."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "Unique Name Before Conflict",
            "code": "UNIQ-PRE",
            "duration_years": 2,
            "total_semesters": 4,
        })

        # Insert conflicting official course directly before approval
        conflict = Course(
            department_id=self.dept_cs.id,
            name="Conflict Course Inserted",
            code="UNIQ-PRE",
            duration_years=2,
            total_semesters=4,
            is_active=True,
        )
        self.db.add(conflict)
        self.db.commit()

        admin_token = self._generate_token(self.user_admin)
        status, data = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/approve", admin_token)
        self.assertEqual(status, 409)

        # Check proposal remains PENDING_APPROVAL
        refreshed_prop = self.db.query(CourseProposal).filter(CourseProposal.id == prop["id"]).first()
        self.assertEqual(refreshed_prop.status, ProposalStatus.PENDING_APPROVAL)

    def test_31_failed_subject_creation_does_not_mark_proposal_approved(self):
        """31. Failed subject creation must not mark proposal APPROVED."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/subject-proposals/", hod_token, {
            "course_id": self.course_mca.id,
            "name": "Subj Conflict Test",
            "code": "SUB-CONF",
            "semester": 1,
            "credits": 3,
        })

        # Insert conflicting official subject directly before approval
        conflict_subj = Subject(
            course_id=self.course_mca.id,
            name="Conflicting Subject Record",
            code="SUB-CONF",
            semester=1,
            credits=3,
            is_active=True,
        )
        self.db.add(conflict_subj)
        self.db.commit()

        admin_token = self._generate_token(self.user_admin)
        status, data = self._request("POST", f"/api/v1/subject-proposals/{prop['id']}/approve", admin_token)
        self.assertEqual(status, 409)

        refreshed_prop = self.db.query(SubjectProposal).filter(SubjectProposal.id == prop["id"]).first()
        self.assertEqual(refreshed_prop.status, ProposalStatus.PENDING_APPROVAL)

    def test_32_approval_is_atomic(self):
        """32. Approval is atomic: no partial updates occur upon failure."""
        hod_token = self._generate_token(self.user_hod_cs)
        _, prop = self._request("POST", "/api/v1/course-proposals/", hod_token, {
            "name": "Atomic Check Course",
            "code": "ATOM-01",
            "duration_years": 2,
            "total_semesters": 4,
        })

        # Deactivate department before approval to trigger failure during approval re-validation
        dept = self.db.query(Department).filter(Department.id == self.dept_cs.id).first()
        dept.is_active = False
        self.db.commit()

        admin_token = self._generate_token(self.user_admin)
        status, _ = self._request("POST", f"/api/v1/course-proposals/{prop['id']}/approve", admin_token)
        self.assertEqual(status, 400)

        # Check proposal is still PENDING_APPROVAL and reviewed_at is None
        refreshed = self.db.query(CourseProposal).filter(CourseProposal.id == prop["id"]).first()
        self.assertEqual(refreshed.status, ProposalStatus.PENDING_APPROVAL)
        self.assertIsNone(refreshed.reviewed_at)


if __name__ == "__main__":
    unittest.main()
