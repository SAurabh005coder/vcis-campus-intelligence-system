from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.attendance import Attendance
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
)

router = APIRouter(
    prefix="/api/v1/attendance",
    tags=["Attendance"],
)


@router.post(
    "/",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_attendance(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.FACULTY,
        )
    ),
):
    # ---------------------------------------------------------
    # 1. Verify enrollment exists
    # ---------------------------------------------------------

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.id == attendance_data.enrollment_id
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found.",
        )

    # ---------------------------------------------------------
    # 2. Verify enrollment is active
    # ---------------------------------------------------------

    if enrollment.status != EnrollmentStatus.ENROLLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance cannot be recorded for a non-enrolled student.",
        )

    # ---------------------------------------------------------
    # 3. Prevent duplicate attendance
    # ---------------------------------------------------------

    existing_attendance = (
        db.query(Attendance)
        .filter(
            Attendance.enrollment_id
            == attendance_data.enrollment_id,
            Attendance.attendance_date
            == attendance_data.attendance_date,
        )
        .first()
    )

    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance has already been recorded for this enrollment on this date.",
        )

    # ---------------------------------------------------------
    # 4. Create attendance
    # ---------------------------------------------------------

    db_attendance = Attendance(
        enrollment_id=attendance_data.enrollment_id,
        attendance_date=attendance_data.attendance_date,
        status=attendance_data.status,
        remarks=attendance_data.remarks,
    )

    db.add(db_attendance)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attendance already exists for this enrollment and date.",
        )

    db.refresh(db_attendance)

    return db_attendance


@router.get(
    "/",
    response_model=list[AttendanceResponse],
)
def get_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
):
    query = db.query(Attendance)

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        query = (
            query.join(
                Enrollment,
                Attendance.enrollment_id == Enrollment.id,
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
    "/{attendance_id}",
    response_model=AttendanceResponse,
)
def get_attendance_record(
    attendance_id: int,
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
                detail="You do not have permission to access this attendance record.",
            )

        attendance = (
            db.query(Attendance)
            .join(Enrollment, Attendance.enrollment_id == Enrollment.id)
            .filter(
                Attendance.id == attendance_id,
                Enrollment.student_id == student.id,
            )
            .first()
        )

        if attendance is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this attendance record.",
            )

        return attendance

    attendance = (
        db.query(Attendance)
        .filter(Attendance.id == attendance_id)
        .first()
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found.",
        )

    if current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student = (
            db.query(Student)
            .join(Enrollment, Student.id == Enrollment.student_id)
            .filter(Enrollment.id == attendance.enrollment_id)
            .first()
        )
        if student is None or student.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access attendance records outside your department.",
            )

    return attendance


@router.put(
    "/{attendance_id}",
    response_model=AttendanceResponse,
)
def update_attendance(
    attendance_id: int,
    attendance_data: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            UserRole.ADMIN,
            UserRole.FACULTY,
        )
    ),
):
    attendance = (
        db.query(Attendance)
        .filter(Attendance.id == attendance_id)
        .first()
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found.",
        )

    attendance.status = attendance_data.status
    attendance.remarks = attendance_data.remarks

    db.commit()
    db.refresh(attendance)

    return attendance


@router.delete(
    "/{attendance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attendance(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    attendance = (
        db.query(Attendance)
        .filter(Attendance.id == attendance_id)
        .first()
    )

    if attendance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found.",
        )

    db.delete(attendance)
    db.commit()

    return None