from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.assessment import Assessment
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentResponse,
    AssessmentUpdate,
)

router = APIRouter(
    prefix="/api/v1/assessments",
    tags=["Assessments"],
)


@router.post(
    "/",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment(
    assessment_data: AssessmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.ADMIN,
        )
    ),
):
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.id == assessment_data.enrollment_id)
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    if enrollment.status != EnrollmentStatus.ENROLLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment cannot be recorded for a non-enrolled student.",
        )

    if assessment_data.obtained_marks > assessment_data.max_marks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Obtained marks cannot exceed maximum marks.",
        )

    assessment = Assessment(
        enrollment_id=assessment_data.enrollment_id,
        assessment_type=assessment_data.assessment_type,
        assessment_name=assessment_data.assessment_name,
        max_marks=assessment_data.max_marks,
        obtained_marks=assessment_data.obtained_marks,
        assessment_date=assessment_data.assessment_date,
        remarks=assessment_data.remarks,
    )

    db.add(assessment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment already exists for the enrollment.",
        )

    db.refresh(assessment)

    return assessment


@router.get(
    "/",
    response_model=list[AssessmentResponse],
)
def get_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    query = db.query(Assessment)

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        query = (
            query.join(
                Enrollment,
                Assessment.enrollment_id == Enrollment.id,
            )
            .join(
                Student,
                Enrollment.student_id == Student.id,
            )
            .filter(
                Student.department_id == hod_department_id,
            )
        )

    return query.all()


@router.get(
    "/{assessment_id}",
    response_model=AssessmentResponse,
)
def get_assessment(
    assessment_id: int,
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
                detail="You do not have permission to access this assessment record.",
            )

        assessment = (
            db.query(Assessment)
            .join(Enrollment, Assessment.enrollment_id == Enrollment.id)
            .filter(
                Assessment.id == assessment_id,
                Enrollment.student_id == student.id,
            )
            .first()
        )

        if assessment is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this assessment record.",
            )

        return assessment

    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == assessment_id)
        .first()
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student = (
            db.query(Student)
            .join(Enrollment, Student.id == Enrollment.student_id)
            .filter(Enrollment.id == assessment.enrollment_id)
            .first()
        )
        if student is None or student.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access assessments outside your department.",
            )

    return assessment


@router.put(
    "/{assessment_id}",
    response_model=AssessmentResponse,
)
def update_assessment(
    assessment_id: int,
    assessment_data: AssessmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.ADMIN,
        )
    ),
):
    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == assessment_id)
        .first()
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.id == assessment.enrollment_id)
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    if assessment_data.obtained_marks > assessment_data.max_marks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Obtained marks cannot exceed maximum marks.",
        )

    assessment.assessment_type = assessment_data.assessment_type
    assessment.assessment_name = assessment_data.assessment_name
    assessment.max_marks = assessment_data.max_marks
    assessment.obtained_marks = assessment_data.obtained_marks
    assessment.assessment_date = assessment_data.assessment_date
    assessment.remarks = assessment_data.remarks

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This assessment already exists for the enrollment.",
        )

    db.refresh(assessment)

    return assessment


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == assessment_id)
        .first()
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    db.delete(assessment)
    db.commit()

    return None