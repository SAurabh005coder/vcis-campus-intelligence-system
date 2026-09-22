"""
VCIS 3.0 — Academic Intervention Service

Provides the database and domain logic for creating and retrieving
academic intervention records.

Decoupling Guarantee:
- Does NOT generate predictions or compute features.
- Does NOT alter status classification thresholds.
- Treats trigger_predicted_score and trigger_academic_status strictly as
  supplied historical evidence.
"""

import math
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.faculty import Faculty
from app.models.intervention import Intervention, InterventionStatus, InterventionType
from app.models.student import Student
from app.schemas.intervention import InterventionCreate, InterventionUpdate
from app.services.academic_status_service import AcademicStatus


# ======================================================================
# Domain Exceptions
# ======================================================================

class InterventionServiceError(Exception):
    """Base exception for intervention service operations."""


class InterventionNotFoundError(InterventionServiceError):
    """Raised when the requested intervention record does not exist."""


class StudentNotFoundError(InterventionServiceError):
    """Raised when the target student ID does not match any existing student."""


class FacultyNotFoundError(InterventionServiceError):
    """Raised when the assigned faculty ID does not match any existing faculty."""


class InvalidInterventionDataError(InterventionServiceError, ValueError):
    """Raised when intervention parameters violate validation constraints."""


# ======================================================================
# Service Operations
# ======================================================================

def create_intervention(
    db: Session,
    intervention_data: InterventionCreate,
) -> Intervention:
    """
    Create and persist a new academic intervention record.

    Validates:
    1. Target student exists.
    2. Assigned faculty member exists.
    3. Semester is within student's program range (1 to course.total_semesters).
    4. Trigger predicted score is a finite numeric value (not NaN, Inf, or boolean).

    Allows multiple interventions for the same student and semester.
    """
    # 1. Validate trigger score finiteness
    score = intervention_data.trigger_predicted_score
    if isinstance(score, bool) or not isinstance(score, (int, float)) or math.isnan(score) or math.isinf(score):
        raise InvalidInterventionDataError(
            f"Trigger predicted score must be a finite numeric value. Got: {score}"
        )

    # 2. Verify student existence
    student = db.query(Student).filter(Student.id == intervention_data.student_id).first()
    if student is None:
        raise StudentNotFoundError(
            f"Student with ID {intervention_data.student_id} not found."
        )

    # 3. Validate semester range against student's program (Course)
    course = db.query(Course).filter(Course.id == student.course_id).first()
    max_sem = course.total_semesters if course is not None else 12

    if intervention_data.semester < 1 or intervention_data.semester > max_sem:
        course_label = f" for program '{course.code}'" if course is not None else ""
        raise InvalidInterventionDataError(
            f"Semester must be between 1 and {max_sem}{course_label}. Got: {intervention_data.semester}"
        )

    # 4. Verify faculty existence
    faculty = db.query(Faculty).filter(Faculty.id == intervention_data.faculty_id).first()
    if faculty is None:
        raise FacultyNotFoundError(
            f"Faculty with ID {intervention_data.faculty_id} not found."
        )

    # 5. Persist intervention entity
    intervention = Intervention(
        student_id=intervention_data.student_id,
        faculty_id=intervention_data.faculty_id,
        semester=intervention_data.semester,
        intervention_type=intervention_data.intervention_type,
        status=intervention_data.status,
        trigger_predicted_score=float(score),
        trigger_academic_status=intervention_data.trigger_academic_status,
        description=intervention_data.description,
        action_plan=intervention_data.action_plan,
        follow_up_date=intervention_data.follow_up_date,
    )

    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return intervention


def get_intervention_by_id(
    db: Session,
    intervention_id: int,
) -> Intervention:
    """
    Retrieve an intervention record by its unique primary key ID.

    Raises InterventionNotFoundError if not found.
    """
    if intervention_id <= 0:
        raise InvalidInterventionDataError("Intervention ID must be a positive integer.")

    intervention = (
        db.query(Intervention)
        .filter(Intervention.id == intervention_id)
        .first()
    )

    if intervention is None:
        raise InterventionNotFoundError(
            f"Intervention with ID {intervention_id} not found."
        )

    return intervention


def list_interventions(
    db: Session,
    student_id: int | None = None,
    faculty_id: int | None = None,
    semester: int | None = None,
    status: InterventionStatus | None = None,
    department_id: int | None = None,
) -> list[Intervention]:
    """
    Retrieve a list of interventions with optional filtering.
    """
    query = db.query(Intervention)

    if department_id is not None:
        query = query.join(Student, Intervention.student_id == Student.id).filter(
            Student.department_id == department_id
        )

    if student_id is not None:
        query = query.filter(Intervention.student_id == student_id)
    if faculty_id is not None:
        query = query.filter(Intervention.faculty_id == faculty_id)
    if semester is not None:
        query = query.filter(Intervention.semester == semester)
    if status is not None:
        query = query.filter(Intervention.status == status)

    return query.order_by(Intervention.created_at.desc()).all()


def update_intervention(
    db: Session,
    intervention_id: int,
    update_data: InterventionUpdate,
) -> Intervention:
    """
    Update mutable workflow fields of an existing academic intervention.

    Guarantees trigger_predicted_score and trigger_academic_status remain immutable.
    """
    intervention = get_intervention_by_id(db, intervention_id)

    if update_data.status is not None:
        intervention.status = update_data.status
    if update_data.description is not None:
        intervention.description = update_data.description
    if update_data.action_plan is not None:
        intervention.action_plan = update_data.action_plan
    if update_data.follow_up_date is not None:
        intervention.follow_up_date = update_data.follow_up_date

    db.commit()
    db.refresh(intervention)
    return intervention
