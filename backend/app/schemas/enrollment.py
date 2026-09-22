from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enrollment import EnrollmentStatus


class EnrollmentCreate(BaseModel):
    student_id: int = Field(gt=0)

    subject_id: int = Field(gt=0)

    academic_year: str = Field(
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-\d{2}$",
    )


class EnrollmentUpdate(BaseModel):
    status: EnrollmentStatus


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    academic_year: str
    enrollment_date: datetime
    status: EnrollmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )