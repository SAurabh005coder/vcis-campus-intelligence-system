from sqlalchemy.orm import Session

from app.models.attendance import Attendance, AttendanceStatus
from app.models.assessment import Assessment
from app.models.enrollment import Enrollment
from app.models.subject import Subject


def get_enrollment_result(
    db: Session,
    enrollment_id: int,
):
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.id == enrollment_id)
        .first()
    )

    if enrollment is None:
        return None

    subject = (
        db.query(Subject)
        .filter(Subject.id == enrollment.subject_id)
        .first()
    )

    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.enrollment_id == enrollment_id
        )
        .order_by(Assessment.assessment_date)
        .all()
    )

    total_max_marks = sum(
        assessment.max_marks
        for assessment in assessments
    )

    total_obtained_marks = sum(
        assessment.obtained_marks
        for assessment in assessments
    )

    overall_percentage = (
        (total_obtained_marks / total_max_marks) * 100
        if total_max_marks > 0
        else 0.0
    )

    assessment_results = []

    for assessment in assessments:
        percentage = (
            (assessment.obtained_marks / assessment.max_marks) * 100
            if assessment.max_marks > 0
            else 0.0
        )

        assessment_results.append(
            {
                "assessment_id": assessment.id,
                "assessment_type": assessment.assessment_type.value,
                "assessment_name": assessment.assessment_name,
                "max_marks": assessment.max_marks,
                "obtained_marks": assessment.obtained_marks,
                "percentage": round(percentage, 2),
            }
        )

    return {
        "enrollment_id": enrollment.id,
        "student_id": enrollment.student_id,
        "subject_id": enrollment.subject_id,
        "academic_year": enrollment.academic_year,
        "subject_name": subject.name if subject else None,
        "subject_code": subject.code if subject else None,
        "semester": subject.semester if subject else None,
        "credits": subject.credits if subject else None,
        "total_max_marks": total_max_marks,
        "total_obtained_marks": total_obtained_marks,
        "overall_percentage": round(
            overall_percentage,
            2,
        ),
        "assessments": assessment_results,
    }
    
def get_student_academic_summary(
    db: Session,
    student_id: int,
):
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == student_id)
        .order_by(Enrollment.id)
        .all()
    )

    if not enrollments:
        return None

    subject_results = []

    total_max_marks = 0
    total_obtained_marks = 0

    for enrollment in enrollments:
        result = get_enrollment_result(
            db,
            enrollment.id,
        )

        if result is None:
            continue

        subject_results.append(result)

        total_max_marks += result["total_max_marks"]
        total_obtained_marks += result["total_obtained_marks"]

    overall_percentage = (
        (total_obtained_marks / total_max_marks) * 100
        if total_max_marks > 0
        else 0.0
    )

    return {
        "student_id": student_id,
        "total_subjects": len(subject_results),
        "total_max_marks": total_max_marks,
        "total_obtained_marks": total_obtained_marks,
        "overall_percentage": round(
            overall_percentage,
            2,
        ),
        "subjects": subject_results,
    }
    
    
def get_student_semester_result(
    db: Session,
    student_id: int,
    semester: int,
):
    enrollments = (
        db.query(Enrollment)
        .join(
            Subject,
            Enrollment.subject_id == Subject.id,
        )
        .filter(
            Enrollment.student_id == student_id,
            Subject.semester == semester,
        )
        .order_by(Enrollment.id)
        .all()
    )

    if not enrollments:
        return None

    subject_results = []

    total_max_marks = 0
    total_obtained_marks = 0
    total_credits = 0

    for enrollment in enrollments:
        result = get_enrollment_result(
            db,
            enrollment.id,
        )

        if result is None:
            continue

        subject_results.append(result)

        total_max_marks += result["total_max_marks"]
        total_obtained_marks += result["total_obtained_marks"]

        if result["credits"] is not None:
            total_credits += result["credits"]

    overall_percentage = (
        (total_obtained_marks / total_max_marks) * 100
        if total_max_marks > 0
        else 0.0
    )

    return {
        "student_id": student_id,
        "semester": semester,
        "total_subjects": len(subject_results),
        "total_credits": total_credits,
        "total_max_marks": total_max_marks,
        "total_obtained_marks": total_obtained_marks,
        "overall_percentage": round(
            overall_percentage,
            2,
        ),
        "subjects": subject_results,
    }
    
    
def get_enrollment_attendance(
    db: Session,
    enrollment_id: int,
):
    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.id == enrollment_id)
        .first()
    )

    if enrollment is None:
        return None

    attendance_records = (
        db.query(Attendance)
        .filter(
            Attendance.enrollment_id == enrollment_id
        )
        .all()
    )

    total_classes = len(attendance_records)

    present_classes = sum(
        1
        for record in attendance_records
        if record.status == AttendanceStatus.PRESENT
    )

    absent_classes = sum(
        1
        for record in attendance_records
        if record.status == AttendanceStatus.ABSENT
    )

    attendance_percentage = (
        (present_classes / total_classes) * 100
        if total_classes > 0
        else 0.0
    )

    return {
        "enrollment_id": enrollment_id,
        "total_classes": total_classes,
        "present_classes": present_classes,
        "absent_classes": absent_classes,
        "attendance_percentage": round(
            attendance_percentage,
            2,
        ),
    }
    

def get_enrollment_performance_profile(
    db: Session,
    enrollment_id: int,
):
    result = get_enrollment_result(
        db,
        enrollment_id,
    )

    if result is None:
        return None

    attendance = get_enrollment_attendance(
        db,
        enrollment_id,
    )

    return {
        "enrollment_id": enrollment_id,
        "student_id": result["student_id"],
        "subject_id": result["subject_id"],
        "academic_year": result["academic_year"],
        "subject_name": result["subject_name"],
        "subject_code": result["subject_code"],
        "semester": result["semester"],
        "credits": result["credits"],
        "assessment_percentage": result["overall_percentage"],
        "attendance_percentage": (
            attendance["attendance_percentage"]
            if attendance
            else 0.0
        ),
        "total_classes": (
            attendance["total_classes"]
            if attendance
            else 0
        ),
        "present_classes": (
            attendance["present_classes"]
            if attendance
            else 0
        ),
        "absent_classes": (
            attendance["absent_classes"]
            if attendance
            else 0
        ),
    }