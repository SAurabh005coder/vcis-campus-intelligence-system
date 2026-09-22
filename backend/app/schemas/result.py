from pydantic import BaseModel


class AssessmentResultItem(BaseModel):
    assessment_id: int
    assessment_type: str
    assessment_name: str
    max_marks: int
    obtained_marks: int
    percentage: float


class EnrollmentResultResponse(BaseModel):
    enrollment_id: int
    student_id: int
    subject_id: int
    academic_year: str

    subject_name: str | None
    subject_code: str | None
    semester: int | None
    credits: int | None

    total_max_marks: int
    total_obtained_marks: int
    overall_percentage: float

    assessments: list[AssessmentResultItem]
    
    
class StudentAcademicSummaryResponse(BaseModel):
    student_id: int
    total_subjects: int
    total_max_marks: int
    total_obtained_marks: int
    overall_percentage: float
    subjects: list[EnrollmentResultResponse]
    
    
class StudentSemesterResultResponse(BaseModel):
    student_id: int
    semester: int
    total_subjects: int
    total_credits: int
    total_max_marks: int
    total_obtained_marks: int
    overall_percentage: float
    subjects: list[EnrollmentResultResponse]
    
class EnrollmentPerformanceProfileResponse(BaseModel):
    enrollment_id: int
    student_id: int
    subject_id: int
    academic_year: str
    subject_name: str | None
    subject_code: str | None
    semester: int | None
    credits: int | None
    assessment_percentage: float
    attendance_percentage: float
    total_classes: int
    present_classes: int
    absent_classes: int