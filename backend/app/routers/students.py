from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.course import Course
from app.models.department import Department
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.student import (
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)

router = APIRouter(
    prefix="/api/v1/students",
    tags=["Students"],
)


@router.post(
    "/",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    # Verify User exists
    user = (
        db.query(User)
        .filter(User.id == student.user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected user must have STUDENT role.",
        )

    # Prevent one User from having multiple Student profiles
    existing_student = (
        db.query(Student)
        .filter(Student.user_id == student.user_id)
        .first()
    )

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user already has a student profile.",
        )

    # Verify Department
    department = (
        db.query(Department)
        .filter(
            Department.id == student.department_id,
            Department.is_active.is_(True),
        )
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active department not found.",
        )

    # Verify Course
    course = (
        db.query(Course)
        .filter(
            Course.id == student.course_id,
            Course.is_active.is_(True),
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active course not found.",
        )

    # Ensure Course belongs to selected Department
    if course.department_id != student.department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course does not belong to the selected department.",
        )

    db_student = Student(
        user_id=student.user_id,
        department_id=student.department_id,
        course_id=student.course_id,
        roll_number=student.roll_number,
        admission_year=student.admission_year,
        current_semester=student.current_semester,
        name=student.name,
        email=student.email,
        is_active=True,
    )

    db.add(db_student)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email or roll number already exists.",
        )

    db.refresh(db_student)

    return db_student


@router.get(
    "/",
    response_model=list[StudentResponse],
)
def get_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    query = db.query(Student)

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        query = query.filter(Student.department_id == hod_department_id)

    return query.all()


@router.get(
    "/me",
    response_model=StudentResponse,
)
def get_current_student_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.STUDENT,
        )
    ),
):
    student = (
        db.query(Student)
        .filter(Student.user_id == current_user.id)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found.",
        )

    return student


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
)
def get_student(
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
    if current_user.role == UserRole.STUDENT:
        student_record = (
            db.query(Student)
            .filter(Student.user_id == current_user.id)
            .first()
        )
        if student_record is None or student_record.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this student profile.",
            )
        return student_record

    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        if student.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access students outside your department.",
            )

    return student


@router.put(
    "/{student_id}",
    response_model=StudentResponse,
)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    department = (
        db.query(Department)
        .filter(
            Department.id == student_data.department_id,
            Department.is_active.is_(True),
        )
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active department not found.",
        )

    course = (
        db.query(Course)
        .filter(
            Course.id == student_data.course_id,
            Course.is_active.is_(True),
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active course not found.",
        )

    if course.department_id != student_data.department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course does not belong to the selected department.",
        )

    student.department_id = student_data.department_id
    student.course_id = student_data.course_id
    student.roll_number = student_data.roll_number
    student.admission_year = student_data.admission_year
    student.current_semester = student_data.current_semester
    student.name = student_data.name
    student.email = student_data.email
    student.is_active = student_data.is_active

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email or roll number already exists.",
        )

    db.refresh(student)

    return student


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found.",
        )

    db.delete(student)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete student with existing academic records or enrollments.",
        )

    return None