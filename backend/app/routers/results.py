from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.subject import Subject
from app.models.user import User, UserRole
from app.schemas.result import (
    EnrollmentPerformanceProfileResponse,
    EnrollmentResultResponse,
    StudentAcademicSummaryResponse,
    StudentSemesterResultResponse,
)
from app.services.result_service import (
    get_enrollment_performance_profile,
    get_enrollment_result,
    get_student_academic_summary,
    get_student_semester_result,
)

router = APIRouter(
    prefix="/api/v1/results",
    tags=["Results"],
)


def _verify_student_ownership(
    db: Session,
    current_user: User,
    requested_student_id: int,
) -> None:
    if current_user.role == UserRole.STUDENT:
        student_record = (
            db.query(Student)
            .filter(Student.user_id == current_user.id)
            .first()
        )
        if student_record is None or student_record.id != requested_student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access these results.",
            )
    elif current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student_record = (
            db.query(Student)
            .filter(Student.id == requested_student_id)
            .first()
        )
        if student_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found.",
            )
        if student_record.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access results outside your department.",
            )


def _verify_enrollment_ownership(
    db: Session,
    current_user: User,
    enrollment: Enrollment,
) -> None:
    if current_user.role == UserRole.STUDENT:
        student_record = (
            db.query(Student)
            .filter(Student.user_id == current_user.id)
            .first()
        )
        if student_record is None or enrollment.student_id != student_record.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this enrollment result.",
            )
    elif current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student_record = (
            db.query(Student)
            .filter(Student.id == enrollment.student_id)
            .first()
        )
        if student_record is None or student_record.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access results outside your department.",
            )



@router.get(
    "/",
    response_model=list[EnrollmentResultResponse],
)
def get_results(
    student_id: int | None = None,
    enrollment_id: int | None = None,
    subject_id: int | None = None,
    course_id: int | None = None,
    semester: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    query = (
        db.query(Enrollment)
        .join(
            Student,
            Enrollment.student_id == Student.id,
        )
    )

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        query = query.filter(
            Student.department_id == hod_department_id,
        )

    if student_id is not None:
        query = query.filter(Enrollment.student_id == student_id)

    if enrollment_id is not None:
        query = query.filter(Enrollment.id == enrollment_id)

    if subject_id is not None:
        query = query.filter(Enrollment.subject_id == subject_id)

    if course_id is not None:
        query = query.filter(Student.course_id == course_id)

    if semester is not None:
        query = query.join(
            Subject,
            Enrollment.subject_id == Subject.id,
        ).filter(
            Subject.semester == semester,
        )

    enrollments = query.all()

    results = []
    for enrollment in enrollments:
        result = get_enrollment_result(
            db,
            enrollment.id,
        )
        if result is not None:
            results.append(result)

    return results


@router.get(
    "/enrollment/{enrollment_id}",
    response_model=EnrollmentResultResponse,
)
def get_enrollment_result_endpoint(
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
    if enrollment_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid enrollment ID.",
        )

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

    _verify_enrollment_ownership(db, current_user, enrollment)

    result = get_enrollment_result(
        db,
        enrollment_id,
    )

    return result


@router.get(
    "/student/{student_id}/summary",
    response_model=StudentAcademicSummaryResponse,
)
def get_student_academic_summary_endpoint(
    student_id: int,
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
    if student_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student ID.",
        )

    _verify_student_ownership(db, current_user, student_id)

    result = get_student_academic_summary(
        db,
        student_id,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student has no enrollments.",
        )

    return result


@router.get(
    "/student/{student_id}/semester/{semester}",
    response_model=StudentSemesterResultResponse,
)
def get_student_semester_result_endpoint(
    student_id: int,
    semester: int,
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
    if student_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student ID.",
        )

    if semester <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid semester.",
        )

    _verify_student_ownership(db, current_user, student_id)

    result = get_student_semester_result(
        db,
        student_id,
        semester,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No enrollments found for this student and semester.",
        )

    return result


@router.get(
    "/enrollment/{enrollment_id}/performance",
    response_model=EnrollmentPerformanceProfileResponse,
)
def get_enrollment_performance_profile_endpoint(
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
    if enrollment_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid enrollment ID.",
        )

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

    _verify_enrollment_ownership(db, current_user, enrollment)

    result = get_enrollment_performance_profile(
        db,
        enrollment_id,
    )

    return result