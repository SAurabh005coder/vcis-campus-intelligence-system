from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles
from app.database import get_db
from app.models.department import Department
from app.models.user import UserRole
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)


router = APIRouter(
    prefix="/api/v1/departments",
    tags=["Departments"],
)


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    department = Department(
        name=department_data.name,
        code=department_data.code,
        description=department_data.description,
    )

    db.add(department)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A department with this name or code already exists.",
        )

    db.refresh(department)

    return department


@router.get(
    "/",
    response_model=list[DepartmentResponse],
)
def get_departments(
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
    return db.query(Department).all()


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
)
def get_department(
    department_id: int,
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
    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    return department


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
)
def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    department.name = department_data.name
    department.code = department_data.code
    department.description = department_data.description
    department.is_active = department_data.is_active

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A department with this name or code already exists.",
        )

    db.refresh(department)

    return department


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    department = (
        db.query(Department)
        .filter(Department.id == department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    db.delete(department)
    db.commit()

    return None