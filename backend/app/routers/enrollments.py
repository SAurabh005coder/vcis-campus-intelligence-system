from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User, UserRole
from app.schemas.enrollment import (
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentUpdate,
)

router = APIRouter(
    prefix="/api/v1/enrollments",
    tags=["Enrollments"],
)


@router.post(
    "/",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    # ---------------------------------------------------------
    # 1. Verify Student
    # ---------------------------------------------------------

    student = (
        db.query(Student)
        .filter(Student.id == enrollment_data.student_id)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    if not student.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is inactive.",
        )

    # ---------------------------------------------------------
    # 2. Verify Subject
    # ---------------------------------------------------------

    subject = (
        db.query(Subject)
        .filter(Subject.id == enrollment_data.subject_id)
        .first()
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found.",
        )

    if not subject.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject is inactive.",
        )

    # ---------------------------------------------------------
    # 3. Verify Course compatibility
    # ---------------------------------------------------------

    if student.course_id != subject.course_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject does not belong to the student's course.",
        )

    # ---------------------------------------------------------
    # 4. Verify Semester compatibility
    # ---------------------------------------------------------

    if student.current_semester != subject.semester:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject does not belong to the student's current semester.",
        )

    # ---------------------------------------------------------
    # 5. Prevent duplicate enrollment
    # ---------------------------------------------------------

    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == enrollment_data.student_id,
            Enrollment.subject_id == enrollment_data.subject_id,
            Enrollment.academic_year
            == enrollment_data.academic_year,
        )
        .first()
    )

    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this subject for this academic year.",
        )

    # ---------------------------------------------------------
    # 6. Create enrollment
    # ---------------------------------------------------------

    db_enrollment = Enrollment(
        student_id=enrollment_data.student_id,
        subject_id=enrollment_data.subject_id,
        academic_year=enrollment_data.academic_year,
        status=EnrollmentStatus.ENROLLED,
    )

    db.add(db_enrollment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Enrollment already exists.",
        )

    db.refresh(db_enrollment)

    return db_enrollment


@router.get(
    "/",
    response_model=list[EnrollmentResponse],
)
def get_enrollments(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    query = db.query(Enrollment)

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        query = query.join(
            Student,
            Enrollment.student_id == Student.id,
        ).filter(
            Student.department_id == hod_department_id,
        )

    return query.all()


@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
)
def get_enrollment(
    enrollment_id: int,
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
    if current_user.role == UserRole.STUDENT:
        student = (
            db.query(Student)
            .filter(Student.user_id == current_user.id)
            .first()
        )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this enrollment.",
            )

        enrollment = (
            db.query(Enrollment)
            .filter(
                Enrollment.id == enrollment_id,
                Enrollment.student_id == student.id,
            )
            .first()
        )

        if enrollment is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this enrollment.",
            )

        return enrollment

    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.id == enrollment_id)
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student = (
            db.query(Student)
            .filter(Student.id == enrollment.student_id)
            .first()
        )
        if student is None or student.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access enrollments outside your department.",
            )

    return enrollment


@router.put(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
)
def update_enrollment(
    enrollment_id: int,
    enrollment_data: EnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.id == enrollment_id)
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    enrollment.status = enrollment_data.status

    db.commit()
    db.refresh(enrollment)

    return enrollment


@router.delete(
    "/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.id == enrollment_id)
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    db.delete(enrollment)
    db.commit()

    return None