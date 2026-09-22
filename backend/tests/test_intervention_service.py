"""
Automated unit tests for VCIS 3.0 Academic Intervention Service & Model.

Validates:
1. Intervention creation.
2. Default status is ASSIGNED.
3. Student foreign-key reference works.
4. Faculty foreign-key reference works.
5. Semester 1 accepted.
6. Semester 4 accepted.
7. Semester 0 rejected.
8. Semester 5 rejected.
9. All four intervention types accepted.
10. All four intervention statuses accepted where appropriate.
11. Trigger predicted score is stored without display rounding.
12. Trigger academic status is stored.
13. Description/action_plan/follow_up_date work.
14. Intervention retrieval works.
15. Missing intervention raises InterventionNotFoundError.
16. Multiple interventions for the same student and semester are allowed.
17. Trigger score NaN/infinity rejected.
18. Boolean trigger score rejected.
19. InterventionUpdate cannot freely modify trigger evidence.
"""

from datetime import date, datetime
import math
import os
import sys
import unittest

from pydantic import ValidationError
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
from app.models.intervention import Intervention, InterventionStatus, InterventionType
from app.services.academic_status_service import AcademicStatus
from app.schemas.intervention import (
    InterventionCreate,
    InterventionUpdate,
    InterventionResponse,
)
from app.services.intervention_service import (
    create_intervention,
    get_intervention_by_id,
    list_interventions,
    InterventionNotFoundError,
    InvalidInterventionDataError,
    StudentNotFoundError,
    FacultyNotFoundError,
)


class TestInterventionService(unittest.TestCase):
    """Unit test suite for Academic Intervention service and database persistence."""

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
        """Clean up SQLite database engine."""
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()

    def setUp(self):
        """Clean database and set up base fixtures before each test."""
        self.db = self.Session()
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()

        # Create base departmental / course setup
        self.dept = Department(id=1, name="Computer Science", code="CS")
        self.course = Course(id=1, department_id=1, name="Master of Computer Applications", code="MCA", duration_years=2, total_semesters=4)
        self.db.add_all([self.dept, self.course])
        self.db.commit()

        # Create test users
        self.user_faculty = User(id=1, email="faculty@test.com", password_hash="hash1", role=UserRole.FACULTY, is_active=True)
        self.user_student = User(id=2, email="student@test.com", password_hash="hash2", role=UserRole.STUDENT, is_active=True)
        self.db.add_all([self.user_faculty, self.user_student])
        self.db.commit()

        # Create faculty and student records
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
        self.student = Student(
            id=1,
            user_id=2,
            department_id=1,
            course_id=1,
            roll_number="MCA2024001",
            admission_year=2024,
            current_semester=1,
            name="Ada Lovelace",
            email="student@test.com",
            is_active=True,
        )
        self.db.add_all([self.faculty, self.student])
        self.db.commit()

    def tearDown(self):
        """Close session."""
        self.db.close()

    # ------------------------------------------------------------------
    # TESTS
    # ------------------------------------------------------------------

    def test_01_intervention_creation_success(self):
        """Verify successful creation of an intervention entity."""
        data = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.EXTRA_CLASS,
            trigger_predicted_score=48.75,
            trigger_academic_status=AcademicStatus.INTERVENTION,
            description="Low test 1 marks.",
            action_plan="Attend 4 remedial lectures.",
            follow_up_date=date(2024, 10, 15),
        )

        created = create_intervention(self.db, data)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.student_id, 1)
        self.assertEqual(created.faculty_id, 1)
        self.assertEqual(created.semester, 1)
        self.assertEqual(created.intervention_type, InterventionType.EXTRA_CLASS)
        self.assertEqual(created.status, InterventionStatus.ASSIGNED)
        self.assertEqual(created.trigger_predicted_score, 48.75)
        self.assertEqual(created.trigger_academic_status, AcademicStatus.INTERVENTION)
        self.assertEqual(created.description, "Low test 1 marks.")
        self.assertEqual(created.action_plan, "Attend 4 remedial lectures.")
        self.assertEqual(created.follow_up_date, date(2024, 10, 15))
        self.assertIsInstance(created.created_at, datetime)
        self.assertIsInstance(created.updated_at, datetime)

    def test_02_default_status_is_assigned(self):
        """Verify that newly created interventions default to ASSIGNED status."""
        data = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=2,
            intervention_type=InterventionType.MONITORING,
            trigger_predicted_score=54.2,
            trigger_academic_status=AcademicStatus.MONITOR,
        )
        created = create_intervention(self.db, data)
        self.assertEqual(created.status, InterventionStatus.ASSIGNED)

    def test_03_student_foreign_key_validation(self):
        """Verify that non-existent student ID raises StudentNotFoundError."""
        data = InterventionCreate(
            student_id=999,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.COUNSELLING,
            trigger_predicted_score=45.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        with self.assertRaises(StudentNotFoundError):
            create_intervention(self.db, data)

    def test_04_faculty_foreign_key_validation(self):
        """Verify that non-existent faculty ID raises FacultyNotFoundError."""
        data = InterventionCreate(
            student_id=1,
            faculty_id=999,
            semester=1,
            intervention_type=InterventionType.COUNSELLING,
            trigger_predicted_score=45.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        with self.assertRaises(FacultyNotFoundError):
            create_intervention(self.db, data)

    def test_05_semester_1_accepted(self):
        """Verify that boundary Semester 1 is accepted."""
        data = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.ADDITIONAL_ASSIGNMENT,
            trigger_predicted_score=52.0,
            trigger_academic_status=AcademicStatus.MONITOR,
        )
        created = create_intervention(self.db, data)
        self.assertEqual(created.semester, 1)

    def test_06_semester_4_accepted(self):
        """Verify that boundary Semester 4 is accepted."""
        data = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=4,
            intervention_type=InterventionType.ADDITIONAL_ASSIGNMENT,
            trigger_predicted_score=52.0,
            trigger_academic_status=AcademicStatus.MONITOR,
        )
        created = create_intervention(self.db, data)
        self.assertEqual(created.semester, 4)

    def test_07_semester_0_rejected(self):
        """Verify that Semester 0 is rejected via schema validation and service validation."""
        # Schema layer validation
        with self.assertRaises(ValidationError):
            InterventionCreate(
                student_id=1,
                faculty_id=1,
                semester=0,
                intervention_type=InterventionType.EXTRA_CLASS,
                trigger_predicted_score=45.0,
                trigger_academic_status=AcademicStatus.INTERVENTION,
            )

    def test_08_semester_5_rejected_for_mca(self):
        """Verify that Semester 5 is rejected for MCA student via program-aware service validation."""
        data = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=5,
            intervention_type=InterventionType.EXTRA_CLASS,
            trigger_predicted_score=45.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        with self.assertRaises(InvalidInterventionDataError):
            create_intervention(self.db, data)

    def test_08b_btech_multi_semester_intervention(self):
        """Verify that B.Tech students support Semesters 1 through 8, and reject Semester 9."""
        course_btech = Course(
            id=2,
            department_id=1,
            name="B.Tech Computer Science",
            code="BTCSE",
            duration_years=4,
            total_semesters=8,
        )
        user_btech = User(id=3, email="btech@test.com", password_hash="hash3", role=UserRole.STUDENT, is_active=True)
        student_btech = Student(
            id=2,
            user_id=3,
            department_id=1,
            course_id=2,
            roll_number="BT2024001",
            admission_year=2024,
            current_semester=5,
            name="Grace Hopper",
            email="btech@test.com",
            is_active=True,
        )
        self.db.add_all([course_btech, user_btech, student_btech])
        self.db.commit()

        # S5 accepted for B.Tech
        data_s5 = InterventionCreate(
            student_id=2,
            faculty_id=1,
            semester=5,
            intervention_type=InterventionType.EXTRA_CLASS,
            trigger_predicted_score=49.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        inv_s5 = create_intervention(self.db, data_s5)
        self.assertEqual(inv_s5.semester, 5)

        # S8 accepted for B.Tech
        data_s8 = InterventionCreate(
            student_id=2,
            faculty_id=1,
            semester=8,
            intervention_type=InterventionType.MONITORING,
            trigger_predicted_score=52.0,
            trigger_academic_status=AcademicStatus.MONITOR,
        )
        inv_s8 = create_intervention(self.db, data_s8)
        self.assertEqual(inv_s8.semester, 8)

        # S9 rejected for B.Tech
        data_s9 = InterventionCreate(
            student_id=2,
            faculty_id=1,
            semester=9,
            intervention_type=InterventionType.COUNSELLING,
            trigger_predicted_score=40.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        with self.assertRaises(InvalidInterventionDataError):
            create_intervention(self.db, data_s9)

    def test_09_all_four_intervention_types_accepted(self):
        """Verify all 4 canonical intervention types are accepted and persisted."""
        expected_types = [
            InterventionType.EXTRA_CLASS,
            InterventionType.ADDITIONAL_ASSIGNMENT,
            InterventionType.COUNSELLING,
            InterventionType.MONITORING,
        ]

        for itype in expected_types:
            with self.subTest(itype=itype):
                data = InterventionCreate(
                    student_id=1,
                    faculty_id=1,
                    semester=1,
                    intervention_type=itype,
                    trigger_predicted_score=49.0,
                    trigger_academic_status=AcademicStatus.INTERVENTION,
                )
                created = create_intervention(self.db, data)
                self.assertEqual(created.intervention_type, itype)

    def test_10_all_four_intervention_statuses_accepted(self):
        """Verify all 4 canonical intervention statuses are accepted."""
        expected_statuses = [
            InterventionStatus.ASSIGNED,
            InterventionStatus.IN_PROGRESS,
            InterventionStatus.COMPLETED,
            InterventionStatus.DISMISSED,
        ]

        for st in expected_statuses:
            with self.subTest(status=st):
                data = InterventionCreate(
                    student_id=1,
                    faculty_id=1,
                    semester=2,
                    intervention_type=InterventionType.EXTRA_CLASS,
                    status=st,
                    trigger_predicted_score=45.0,
                    trigger_academic_status=AcademicStatus.INTERVENTION,
                )
                created = create_intervention(self.db, data)
                self.assertEqual(created.status, st)

    def test_11_trigger_predicted_score_stored_without_rounding(self):
        """Verify trigger predicted score stores exact precision without display rounding."""
        precise_score = 59.999123
        data = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.MONITORING,
            trigger_predicted_score=precise_score,
            trigger_academic_status=AcademicStatus.MONITOR,
        )
        created = create_intervention(self.db, data)
        self.assertAlmostEqual(created.trigger_predicted_score, precise_score, places=5)

    def test_12_trigger_academic_status_stored(self):
        """Verify all canonical AcademicStatus enum values can be stored as trigger evidence."""
        for status_val in [AcademicStatus.NORMAL, AcademicStatus.MONITOR, AcademicStatus.INTERVENTION]:
            with self.subTest(status_val=status_val):
                data = InterventionCreate(
                    student_id=1,
                    faculty_id=1,
                    semester=1,
                    intervention_type=InterventionType.MONITORING,
                    trigger_predicted_score=65.0,
                    trigger_academic_status=status_val,
                )
                created = create_intervention(self.db, data)
                self.assertEqual(created.trigger_academic_status, status_val)

    def test_13_optional_fields_workflow(self):
        """Verify nullable fields description, action_plan, and follow_up_date work properly."""
        data = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.COUNSELLING,
            trigger_predicted_score=42.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
            description="Student struggling with discrete math concepts.",
            action_plan="Weekly 1-on-1 tutoring sessions with faculty mentor.",
            follow_up_date=date(2024, 11, 1),
        )
        created = create_intervention(self.db, data)
        self.assertEqual(created.description, "Student struggling with discrete math concepts.")
        self.assertEqual(created.action_plan, "Weekly 1-on-1 tutoring sessions with faculty mentor.")
        self.assertEqual(created.follow_up_date, date(2024, 11, 1))

    def test_14_intervention_retrieval(self):
        """Verify retrieval of an existing intervention by ID and via listing."""
        data = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.EXTRA_CLASS,
            trigger_predicted_score=48.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        created = create_intervention(self.db, data)

        fetched = get_intervention_by_id(self.db, created.id)
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.student_id, 1)

        items = list_interventions(self.db, student_id=1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, created.id)

    def test_15_missing_intervention_raises_domain_exception(self):
        """Verify get_intervention_by_id raises InterventionNotFoundError when ID is not found."""
        with self.assertRaises(InterventionNotFoundError):
            get_intervention_by_id(self.db, 9999)

        with self.assertRaises(InvalidInterventionDataError):
            get_intervention_by_id(self.db, 0)

    def test_16_multiple_interventions_same_student_and_semester_allowed(self):
        """Verify multiple interventions can coexist for the same student and semester."""
        data1 = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.EXTRA_CLASS,
            trigger_predicted_score=47.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )
        data2 = InterventionCreate(
            student_id=1,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.COUNSELLING,
            trigger_predicted_score=47.0,
            trigger_academic_status=AcademicStatus.INTERVENTION,
        )

        inv1 = create_intervention(self.db, data1)
        inv2 = create_intervention(self.db, data2)

        self.assertNotEqual(inv1.id, inv2.id)
        self.assertEqual(inv1.student_id, inv2.student_id)
        self.assertEqual(inv1.semester, inv2.semester)
        all_sem1 = list_interventions(self.db, student_id=1, semester=1)
        self.assertEqual(len(all_sem1), 2)

    def test_17_trigger_score_nan_and_inf_rejected(self):
        """Verify NaN, +Inf, -Inf are strictly rejected."""
        for invalid_val in [float("nan"), float("inf"), float("-inf")]:
            with self.subTest(invalid_val=invalid_val):
                with self.assertRaises(ValidationError):
                    InterventionCreate(
                        student_id=1,
                        faculty_id=1,
                        semester=1,
                        intervention_type=InterventionType.MONITORING,
                        trigger_predicted_score=invalid_val,
                        trigger_academic_status=AcademicStatus.MONITOR,
                    )

    def test_18_boolean_trigger_score_rejected(self):
        """Verify booleans (True/False) are strictly rejected as trigger scores."""
        for bool_val in [True, False]:
            with self.subTest(bool_val=bool_val):
                with self.assertRaises(ValidationError):
                    InterventionCreate(
                        student_id=1,
                        faculty_id=1,
                        semester=1,
                        intervention_type=InterventionType.MONITORING,
                        trigger_predicted_score=bool_val,
                        trigger_academic_status=AcademicStatus.MONITOR,
                    )

    def test_19_intervention_update_cannot_modify_trigger_evidence(self):
        """Verify InterventionUpdate schema does not expose trigger evidence fields."""
        update_schema = InterventionUpdate(
            status=InterventionStatus.IN_PROGRESS,
            description="Updated description",
        )
        # Verify trigger fields are not part of update model fields
        self.assertNotIn("trigger_predicted_score", InterventionUpdate.model_fields)
        self.assertNotIn("trigger_academic_status", InterventionUpdate.model_fields)

        # Verify response serialization handles full model
        res = InterventionResponse(
            id=10,
            student_id=1,
            faculty_id=1,
            semester=1,
            intervention_type=InterventionType.EXTRA_CLASS,
            status=InterventionStatus.ASSIGNED,
            trigger_predicted_score=48.5,
            trigger_academic_status=AcademicStatus.INTERVENTION,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.assertEqual(res.id, 10)
        self.assertEqual(res.trigger_predicted_score, 48.5)


if __name__ == "__main__":
    unittest.main()
