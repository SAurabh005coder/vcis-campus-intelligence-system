from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles
from app.database import get_db
from app.models.department import Department
from app.models.faculty import Faculty
from app.models.user import User, UserRole
from app.schemas.faculty import (
    FacultyCreate,
    FacultyResponse,
    FacultyUpdate,
)


router = APIRouter(
    prefix="/api/v1/faculty",
    tags=["Faculty"],
)


@router.post(
    "/",
    response_model=FacultyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_faculty(
    faculty_data: FacultyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    user = (
        db.query(User)
        .filter(User.id == faculty_data.user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.role not in (UserRole.FACULTY, UserRole.HOD):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected user does not have an eligible role (must be faculty or hod).",
        )

    existing_faculty = (
        db.query(Faculty)
        .filter(Faculty.user_id == faculty_data.user_id)
        .first()
    )

    if existing_faculty:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user already has a faculty profile.",
        )

    department = (
        db.query(Department)
        .filter(
            Department.id == faculty_data.department_id,
            Department.is_active.is_(True),
        )
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active department not found.",
        )

    existing_employee = (
        db.query(Faculty)
        .filter(
            Faculty.employee_code
            == faculty_data.employee_code
        )
        .first()
    )

    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A faculty member with this employee code already exists.",
        )

    faculty = Faculty(
        user_id=faculty_data.user_id,
        department_id=faculty_data.department_id,
        employee_code=faculty_data.employee_code,
        first_name=faculty_data.first_name,
        last_name=faculty_data.last_name,
        designation=faculty_data.designation,
        phone=faculty_data.phone,
    )

    db.add(faculty)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Faculty record conflicts with an existing record.",
        )

    db.refresh(faculty)

    return faculty


@router.get(
    "/",
    response_model=list[FacultyResponse],
)
def get_faculty(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.STUDENT,
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    return db.query(Faculty).all()


@router.get(
    "/{faculty_id}",
    response_model=FacultyResponse,
)
def get_faculty_member(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.STUDENT,
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    faculty = (
        db.query(Faculty)
        .filter(Faculty.id == faculty_id)
        .first()
    )

    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty member not found.",
        )

    return faculty


@router.put(
    "/{faculty_id}",
    response_model=FacultyResponse,
)
def update_faculty(
    faculty_id: int,
    faculty_data: FacultyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    faculty = (
        db.query(Faculty)
        .filter(Faculty.id == faculty_id)
        .first()
    )

    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty member not found.",
        )

    department = (
        db.query(Department)
        .filter(
            Department.id == faculty_data.department_id,
            Department.is_active.is_(True),
        )
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active department not found.",
        )

    existing_employee = (
        db.query(Faculty)
        .filter(
            Faculty.employee_code
            == faculty_data.employee_code,
            Faculty.id != faculty_id,
        )
        .first()
    )

    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A faculty member with this employee code already exists.",
        )

    faculty.department_id = faculty_data.department_id
    faculty.employee_code = faculty_data.employee_code
    faculty.first_name = faculty_data.first_name
    faculty.last_name = faculty_data.last_name
    faculty.designation = faculty_data.designation
    faculty.phone = faculty_data.phone
    faculty.is_active = faculty_data.is_active

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Faculty record conflicts with an existing record.",
        )

    db.refresh(faculty)

    return faculty


@router.delete(
    "/{faculty_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    faculty = (
        db.query(Faculty)
        .filter(Faculty.id == faculty_id)
        .first()
    )

    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty member not found.",
        )

    db.delete(faculty)
    db.commit()

    return None