from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles
from app.database import get_db
from app.models.course import Course
from app.models.department import Department
from app.models.user import UserRole
from app.schemas.course import (
    CourseCreate,
    CourseResponse,
    CourseUpdate,
)


router = APIRouter(
    prefix="/api/v1/courses",
    tags=["Courses"],
)


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    department = (
        db.query(Department)
        .filter(
            Department.id == course_data.department_id,
            Department.is_active.is_(True),
        )
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active department not found.",
        )

    existing_name = (
        db.query(Course)
        .filter(Course.name == course_data.name)
        .first()
    )

    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this name already exists.",
        )

    existing_code = (
        db.query(Course)
        .filter(Course.code == course_data.code)
        .first()
    )

    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this code already exists.",
        )

    course = Course(
        department_id=course_data.department_id,
        name=course_data.name,
        code=course_data.code,
        description=course_data.description,
        duration_years=course_data.duration_years,
        total_semesters=course_data.total_semesters,
    )

    db.add(course)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course conflicts with an existing record.",
        )

    db.refresh(course)

    return course


@router.get(
    "/",
    response_model=list[CourseResponse],
)
def get_courses(
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
    return db.query(Course).all()


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
)
def get_course(
    course_id: int,
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
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    return course


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    department = (
        db.query(Department)
        .filter(
            Department.id == course_data.department_id,
            Department.is_active.is_(True),
        )
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active department not found.",
        )

    existing_name = (
        db.query(Course)
        .filter(
            Course.name == course_data.name,
            Course.id != course_id,
        )
        .first()
    )

    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this name already exists.",
        )

    existing_code = (
        db.query(Course)
        .filter(
            Course.code == course_data.code,
            Course.id != course_id,
        )
        .first()
    )

    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this code already exists.",
        )

    course.department_id = course_data.department_id
    course.name = course_data.name
    course.code = course_data.code
    course.description = course_data.description
    course.duration_years = course_data.duration_years
    course.total_semesters = course_data.total_semesters
    course.is_active = course_data.is_active

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course conflicts with an existing record.",
        )

    db.refresh(course)

    return course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    course = (
        db.query(Course)
        .filter(Course.id == course_id)
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found.",
        )

    db.delete(course)
    db.commit()

    return None