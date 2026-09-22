from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles
from app.database import get_db
from app.models.course import Course
from app.models.subject import Subject
from app.models.user import UserRole
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)


router = APIRouter(
    prefix="/api/v1/subjects",
    tags=["Subjects"],
)


@router.post(
    "/",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    subject_data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    course = (
        db.query(Course)
        .filter(
            Course.id == subject_data.course_id,
            Course.is_active.is_(True),
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active course not found.",
        )

    existing_code = (
        db.query(Subject)
        .filter(Subject.code == subject_data.code)
        .first()
    )

    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A subject with this code already exists.",
        )

    existing_subject = (
        db.query(Subject)
        .filter(
            Subject.course_id == subject_data.course_id,
            Subject.semester == subject_data.semester,
            Subject.name == subject_data.name,
        )
        .first()
    )

    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subject already exists for the course and semester.",
        )

    subject = Subject(
        course_id=subject_data.course_id,
        name=subject_data.name,
        code=subject_data.code,
        semester=subject_data.semester,
        credits=subject_data.credits,
        description=subject_data.description,
    )

    db.add(subject)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject conflicts with an existing record.",
        )

    db.refresh(subject)

    return subject


@router.get(
    "/",
    response_model=list[SubjectResponse],
)
def get_subjects(
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
    return db.query(Subject).all()


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def get_subject(
    subject_id: int,
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
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id)
        .first()
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found.",
        )

    return subject


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id)
        .first()
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found.",
        )

    course = (
        db.query(Course)
        .filter(
            Course.id == subject_data.course_id,
            Course.is_active.is_(True),
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active course not found.",
        )

    existing_code = (
        db.query(Subject)
        .filter(
            Subject.code == subject_data.code,
            Subject.id != subject_id,
        )
        .first()
    )

    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A subject with this code already exists.",
        )

    existing_subject = (
        db.query(Subject)
        .filter(
            Subject.course_id == subject_data.course_id,
            Subject.semester == subject_data.semester,
            Subject.name == subject_data.name,
            Subject.id != subject_id,
        )
        .first()
    )

    if existing_subject:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This subject already exists for the course and semester.",
        )

    subject.course_id = subject_data.course_id
    subject.name = subject_data.name
    subject.code = subject_data.code
    subject.semester = subject_data.semester
    subject.credits = subject_data.credits
    subject.description = subject_data.description
    subject.is_active = subject_data.is_active

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject conflicts with an existing record.",
        )

    db.refresh(subject)

    return subject


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id)
        .first()
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found.",
        )

    db.delete(subject)
    db.commit()

    return None