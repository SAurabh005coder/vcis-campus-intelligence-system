"""
VCIS 3.0 — Academic Intervention REST API Router

Provides endpoints for managing academic interventions:
- POST /api/v1/interventions (Faculty, HOD, Admin)
- GET /api/v1/interventions/{intervention_id} (Student for own record; Faculty, HOD, Admin)
- GET /api/v1/interventions (Student restricted to own records; Faculty, HOD, Admin with filters)
- PATCH /api/v1/interventions/{intervention_id} (Faculty, HOD, Admin)

Security & IDOR Protection:
- Students can only view their own intervention records.
- Cross-student access attempts via URL or query parameters are blocked with HTTP 403 / scoped filtering.
- Historical trigger evidence (trigger_predicted_score, trigger_academic_status) is immutable.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.faculty import Faculty
from app.models.intervention import InterventionStatus
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.intervention import (
    InterventionCreate,
    InterventionResponse,
    InterventionUpdate,
)
from app.services.intervention_service import (
    FacultyNotFoundError,
    InterventionNotFoundError,
    InvalidInterventionDataError,
    StudentNotFoundError,
    create_intervention,
    get_intervention_by_id,
    list_interventions,
    update_intervention,
)

router = APIRouter(
    prefix="/api/v1/interventions",
    tags=["Interventions"],
)


@router.post(
    "/",
    response_model=InterventionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new academic intervention",
)
def create_intervention_endpoint(
    intervention_data: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    """
    Create an academic intervention record assigned to a student.
    Restricted to Faculty, HOD, and Admin.
    Faculty members can only assign interventions to themselves.
    """
    if current_user.role == UserRole.FACULTY:
        faculty = (
            db.query(Faculty)
            .filter(Faculty.user_id == current_user.id)
            .first()
        )
        if faculty is None or intervention_data.faculty_id != faculty.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Faculty can only assign interventions to themselves.",
            )
    elif current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student = (
            db.query(Student)
            .filter(Student.id == intervention_data.student_id)
            .first()
        )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {intervention_data.student_id} not found.",
            )
        if student.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create an intervention for a student outside your department.",
            )

    try:
        return create_intervention(db, intervention_data)
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except FacultyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidInterventionDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{intervention_id}",
    response_model=InterventionResponse,
    summary="Get an intervention by ID",
)
def get_intervention_endpoint(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.STUDENT,
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    """
    Retrieve an intervention by its ID.

    IDOR Protection:
    - Students are strictly verified against the intervention's student_id.
    - If a student tries to access an intervention belonging to another student,
      HTTP 403 Forbidden is returned.
    """
    if intervention_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid intervention ID.",
        )

    try:
        intervention = get_intervention_by_id(db, intervention_id)
    except InterventionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidInterventionDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Enforce IDOR protection for student users
    if current_user.role == UserRole.STUDENT:
        student_record = (
            db.query(Student)
            .filter(Student.user_id == current_user.id)
            .first()
        )
        if student_record is None or intervention.student_id != student_record.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this intervention.",
            )
    elif current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student_record = (
            db.query(Student)
            .filter(Student.id == intervention.student_id)
            .first()
        )
        if student_record is None or student_record.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access an intervention for a student outside your department.",
            )

    return intervention


@router.get(
    "/",
    response_model=list[InterventionResponse],
    summary="List interventions with optional filters",
)
def list_interventions_endpoint(
    student_id: int | None = Query(default=None, gt=0),
    faculty_id: int | None = Query(default=None, gt=0),
    semester: int | None = Query(default=None, ge=1, le=12, description="Filter by semester"),
    status_filter: InterventionStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.STUDENT,
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    """
    List interventions with optional filters.

    IDOR Protection:
    - For students, student_id is strictly locked to their own student identity.
      Any passed student_id parameter is disregarded.
    """
    effective_student_id = student_id
    department_id = None

    if current_user.role == UserRole.STUDENT:
        student_record = (
            db.query(Student)
            .filter(Student.user_id == current_user.id)
            .first()
        )
        if student_record is None:
            return []
        effective_student_id = student_record.id
    elif current_user.role == UserRole.HOD:
        department_id = resolve_hod_department_id(current_user, db)

    return list_interventions(
        db=db,
        student_id=effective_student_id,
        faculty_id=faculty_id,
        semester=semester,
        status=status_filter,
        department_id=department_id,
    )


@router.patch(
    "/{intervention_id}",
    response_model=InterventionResponse,
    summary="Update intervention workflow fields",
)
def update_intervention_endpoint(
    intervention_id: int,
    update_data: InterventionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    """
    Update workflow fields of an intervention.
    Restricted to Faculty, HOD, and Admin.
    Faculty members can only update interventions assigned to themselves.
    Historical trigger evidence fields remain strictly immutable.
    """
    if intervention_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid intervention ID.",
        )

    try:
        intervention = get_intervention_by_id(db, intervention_id)
    except InterventionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidInterventionDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if current_user.role == UserRole.FACULTY:
        faculty = (
            db.query(Faculty)
            .filter(Faculty.user_id == current_user.id)
            .first()
        )
        if faculty is None or intervention.faculty_id != faculty.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update this intervention.",
            )
    elif current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student_record = (
            db.query(Student)
            .filter(Student.id == intervention.student_id)
            .first()
        )
        if student_record is None or student_record.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update an intervention for a student outside your department.",
            )

    try:
        return update_intervention(db, intervention_id, update_data)
    except InterventionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InvalidInterventionDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
