"""
VCIS 3.0 — AI-Powered Campus Intelligence System
Feature Extraction Service (Student + Semester Level)

This module extracts the exact pre-computed feature vectors required by the
validated VCIS ML regression models for Semester 1 (Model 1) and Semesters 2+ (Model 2).

Architecture Rules & Semantic Invariants:
- All features are calculated strictly at the STUDENT + SEMESTER level.
- Subject.semester determines which semester an enrollment belongs to.
- CT1 is identified strictly via structural AssessmentType.CT1 (no string pattern matching).
- CT2 (AssessmentType.CT2) is strictly excluded from early prediction features.
- FINAL (AssessmentType.FINAL) and current semester final results are strictly excluded.
- student_id is an entity identifier only and is NEVER included in the ML feature dictionary.
- No silent zero-filling or synthetic value fabrication: raises InsufficientDataError when
  required academic data is missing.
- No model loading, inference, or prediction logic belongs in this service.
"""

from typing import Any
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.student import Student
from app.models.subject import Subject
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.assessment import Assessment, AssessmentType
from app.services.result_service import get_student_semester_result


# =====================================================================
# CUSTOM EXCEPTIONS
# =====================================================================

class FeatureExtractionError(Exception):
    """Base exception for feature extraction errors."""


class InsufficientDataError(FeatureExtractionError):
    """Raised when required academic data (attendance, assignments, CT1, or previous semester) is missing."""


class UnsupportedSemesterError(FeatureExtractionError, ValueError):
    """Raised when features are requested for an unsupported semester."""


class StudentNotFoundError(FeatureExtractionError):
    """Raised when the specified student does not exist."""


# =====================================================================
# PRIVATE HELPER FUNCTIONS
# =====================================================================

def _verify_student_exists(db: Session, student_id: int) -> Student:
    """Verify student exists in the database and return the student record."""
    student = (
        db.query(Student)
        .filter(Student.id == student_id)
        .first()
    )
    if student is None:
        raise StudentNotFoundError(f"Student with ID {student_id} was not found.")
    return student


def _get_semester_enrollment_ids(
    db: Session,
    student_id: int,
    semester: int,
) -> list[int]:
    """
    Retrieve all enrollment IDs for a student corresponding to subjects in the target semester.
    Traverses Enrollment -> Subject and filters by Subject.semester.
    """
    enrollments = (
        db.query(Enrollment.id)
        .join(Subject, Enrollment.subject_id == Subject.id)
        .filter(
            Enrollment.student_id == student_id,
            Subject.semester == semester,
            Enrollment.status != EnrollmentStatus.DROPPED,
        )
        .all()
    )
    return [e[0] for e in enrollments]


def _calculate_semester_attendance(
    db: Session,
    enrollment_ids: list[int],
    student_id: int,
    semester: int,
    label: str,
) -> float:
    """
    Calculate aggregate attendance percentage across all semester enrollments:
    (total PRESENT sessions / total sessions) * 100.
    """
    attendance_records = (
        db.query(Attendance.status)
        .filter(Attendance.enrollment_id.in_(enrollment_ids))
        .all()
    )

    total_classes = len(attendance_records)
    if total_classes == 0:
        raise InsufficientDataError(
            f"Cannot calculate {label}: student {student_id} has no attendance records "
            f"in semester {semester}."
        )

    present_classes = sum(
        1 for r in attendance_records if r[0] == AttendanceStatus.PRESENT
    )

    attendance_percentage = (present_classes / total_classes) * 100.0
    return round(float(attendance_percentage), 2)


def _calculate_assessment_average_by_type(
    db: Session,
    enrollment_ids: list[int],
    student_id: int,
    semester: int,
    assessment_type: AssessmentType,
    label: str,
) -> float:
    """
    Calculate arithmetic mean of percentage scores for a specific AssessmentType
    across all semester enrollments.

    For each assessment:
        percentage = (obtained_marks / max_marks) * 100
    Then returns the arithmetic mean across all matching assessment records.
    """
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.enrollment_id.in_(enrollment_ids),
            Assessment.assessment_type == assessment_type,
        )
        .all()
    )

    if not assessments:
        raise InsufficientDataError(
            f"Cannot calculate {label}: student {student_id} has no {assessment_type.name} "
            f"assessments in semester {semester}."
        )

    percentages: list[float] = []
    for assessment in assessments:
        if assessment.max_marks <= 0:
            raise InsufficientDataError(
                f"Invalid assessment record (ID: {assessment.id}): max_marks must be greater than 0."
            )
        pct = (assessment.obtained_marks / assessment.max_marks) * 100.0
        percentages.append(pct)

    average = sum(percentages) / len(percentages)
    return round(float(average), 2)


def _get_previous_semester_score(
    db: Session,
    student_id: int,
    previous_semester: int,
) -> float:
    """
    Retrieve the completed previous semester academic score using the existing result_service.
    Uses result_service.get_student_semester_result(db, student_id, previous_semester).
    """
    result = get_student_semester_result(
        db=db,
        student_id=student_id,
        semester=previous_semester,
    )

    if result is None or result.get("total_max_marks", 0) == 0:
        raise InsufficientDataError(
            f"Cannot calculate previous_semester_score: completed academic result for "
            f"previous semester {previous_semester} is not available for student {student_id}."
        )

    return round(float(result["overall_percentage"]), 2)


# =====================================================================
# PUBLIC FEATURE EXTRACTION API
# =====================================================================

def extract_semester_1_features(
    db: Session,
    student_id: int,
) -> dict[str, float]:
    """
    Extract the exact feature dictionary required by Model 1 for Semester 1 students.

    Features:
    - current_attendance
    - current_assignment_average
    - current_ct1_average

    Strict Invariants:
    - Only records for semester 1 are included.
    - CT2 and Final exams are strictly excluded.
    - No previous-semester features exist or are imputed.
    - student_id is not included in the returned dictionary.

    Returns:
        dict[str, float]: Exactly the 3 features expected by Model 1.

    Raises:
        StudentNotFoundError: If student does not exist.
        InsufficientDataError: If enrollments, attendance, assignments, or CT1 records are missing.
    """
    _verify_student_exists(db, student_id)
    semester = 1

    enrollment_ids = _get_semester_enrollment_ids(db, student_id, semester)
    if not enrollment_ids:
        raise InsufficientDataError(
            f"Student {student_id} has no active enrollments in semester {semester}."
        )

    current_attendance = _calculate_semester_attendance(
        db=db,
        enrollment_ids=enrollment_ids,
        student_id=student_id,
        semester=semester,
        label="current_attendance",
    )

    current_assignment_average = _calculate_assessment_average_by_type(
        db=db,
        enrollment_ids=enrollment_ids,
        student_id=student_id,
        semester=semester,
        assessment_type=AssessmentType.ASSIGNMENT,
        label="current_assignment_average",
    )

    current_ct1_average = _calculate_assessment_average_by_type(
        db=db,
        enrollment_ids=enrollment_ids,
        student_id=student_id,
        semester=semester,
        assessment_type=AssessmentType.CT1,
        label="current_ct1_average",
    )

    return {
        "current_attendance": current_attendance,
        "current_assignment_average": current_assignment_average,
        "current_ct1_average": current_ct1_average,
    }


def extract_semesters_2_plus_features(
    db: Session,
    student_id: int,
    semester: int,
) -> dict[str, float]:
    """
    Extract the exact feature dictionary required by Model 2 for students in Semesters 2 and above.

    Features:
    - previous_semester_score
    - previous_semester_attendance
    - current_attendance
    - current_assignment_average
    - current_ct1_average

    Strict Invariants:
    - Previous semester is strictly target_semester - 1.
    - CT2 and Final exams of current semester are strictly excluded.
    - student_id is not included in the returned dictionary.

    Returns:
        dict[str, float]: Exactly the 5 features expected by Model 2.

    Raises:
        UnsupportedSemesterError: If semester < 2 or exceeds student's program duration.
        StudentNotFoundError: If student does not exist.
        InsufficientDataError: If any required current or previous semester records are missing.
    """
    if semester < 2:
        raise UnsupportedSemesterError(
            f"Semester {semester} is not supported for Model 2. Expected semester >= 2."
        )

    student = _verify_student_exists(db, student_id)

    # Validate against course program duration
    course = db.query(Course).filter(Course.id == student.course_id).first()
    if course is None:
        raise UnsupportedSemesterError(
            f"Student {student_id} is not associated with a valid course/program."
        )
    if semester > course.total_semesters:
        raise UnsupportedSemesterError(
            f"Semester {semester} exceeds maximum semester {course.total_semesters} for course '{course.code}'."
        )

    previous_semester = semester - 1

    # --- 1. Previous Semester Features (semester - 1) ---
    previous_semester_score = _get_previous_semester_score(
        db=db,
        student_id=student_id,
        previous_semester=previous_semester,
    )

    prev_enrollment_ids = _get_semester_enrollment_ids(db, student_id, previous_semester)
    if not prev_enrollment_ids:
        raise InsufficientDataError(
            f"Student {student_id} has no active enrollments in previous semester {previous_semester}."
        )

    previous_semester_attendance = _calculate_semester_attendance(
        db=db,
        enrollment_ids=prev_enrollment_ids,
        student_id=student_id,
        semester=previous_semester,
        label="previous_semester_attendance",
    )

    # --- 2. Current Semester Features (target semester) ---
    curr_enrollment_ids = _get_semester_enrollment_ids(db, student_id, semester)
    if not curr_enrollment_ids:
        raise InsufficientDataError(
            f"Student {student_id} has no active enrollments in current semester {semester}."
        )

    current_attendance = _calculate_semester_attendance(
        db=db,
        enrollment_ids=curr_enrollment_ids,
        student_id=student_id,
        semester=semester,
        label="current_attendance",
    )

    current_assignment_average = _calculate_assessment_average_by_type(
        db=db,
        enrollment_ids=curr_enrollment_ids,
        student_id=student_id,
        semester=semester,
        assessment_type=AssessmentType.ASSIGNMENT,
        label="current_assignment_average",
    )

    current_ct1_average = _calculate_assessment_average_by_type(
        db=db,
        enrollment_ids=curr_enrollment_ids,
        student_id=student_id,
        semester=semester,
        assessment_type=AssessmentType.CT1,
        label="current_ct1_average",
    )

    return {
        "previous_semester_score": previous_semester_score,
        "previous_semester_attendance": previous_semester_attendance,
        "current_attendance": current_attendance,
        "current_assignment_average": current_assignment_average,
        "current_ct1_average": current_ct1_average,
    }


def extract_semesters_2_to_4_features(
    db: Session,
    student_id: int,
    semester: int,
) -> dict[str, float]:
    """
    Backward-compatibility wrapper forwarding to extract_semesters_2_plus_features.
    """
    return extract_semesters_2_plus_features(db=db, student_id=student_id, semester=semester)


def extract_ml_features(
    db: Session,
    student_id: int,
    semester: int | None = None,
) -> dict[str, float]:
    """
    Unified dispatcher to extract the appropriate ML feature vector for a student.

    If semester is not provided, the student's current_semester attribute from the database is used.

    Args:
        db: Active database session.
        student_id: The student ID.
        semester: Optional target semester. If None, student.current_semester is used.

    Returns:
        dict[str, float]: Either Model 1 (3 features) or Model 2 (5 features) dictionary.

    Raises:
        StudentNotFoundError: If student does not exist.
        UnsupportedSemesterError: If semester is outside the student's valid program range.
        InsufficientDataError: If any required academic record is missing.
    """
    student = _verify_student_exists(db, student_id)
    target_semester = semester if semester is not None else student.current_semester

    if target_semester < 1:
        raise UnsupportedSemesterError(
            f"Semester {target_semester} is not supported. Semester must be >= 1."
        )

    course = db.query(Course).filter(Course.id == student.course_id).first()
    if course is None:
        raise UnsupportedSemesterError(
            f"Student {student_id} is not associated with a valid course/program."
        )
    if target_semester > course.total_semesters:
        raise UnsupportedSemesterError(
            f"Semester {target_semester} is invalid for course '{course.code}' (max {course.total_semesters})."
        )

    if target_semester == 1:
        return extract_semester_1_features(db=db, student_id=student_id)
    else:
        return extract_semesters_2_plus_features(
            db=db,
            student_id=student_id,
            semester=target_semester,
        )