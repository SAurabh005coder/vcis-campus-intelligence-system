from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.assessment import AssessmentType


class AssessmentCreate(BaseModel):
    enrollment_id: int = Field(gt=0)

    assessment_type: AssessmentType

    assessment_name: str = Field(
        min_length=2,
        max_length=150,
    )

    max_marks: int = Field(
        gt=0,
        le=1000,
    )

    obtained_marks: int = Field(
        ge=0,
        le=1000,
    )

    assessment_date: date

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )

    @model_validator(mode="after")
    def validate_marks(self):
        if self.obtained_marks > self.max_marks:
            raise ValueError(
                "Obtained marks cannot exceed maximum marks."
            )

        return self


class AssessmentUpdate(BaseModel):
    assessment_type: AssessmentType

    assessment_name: str = Field(
        min_length=2,
        max_length=150,
    )

    max_marks: int = Field(
        gt=0,
        le=1000,
    )

    obtained_marks: int = Field(
        ge=0,
        le=1000,
    )

    assessment_date: date

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )

    @model_validator(mode="after")
    def validate_marks(self):
        if self.obtained_marks > self.max_marks:
            raise ValueError(
                "Obtained marks cannot exceed maximum marks."
            )

        return self


class AssessmentResponse(BaseModel):
    id: int
    enrollment_id: int
    assessment_type: AssessmentType
    assessment_name: str
    max_marks: int
    obtained_marks: int
    assessment_date: date
    remarks: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )