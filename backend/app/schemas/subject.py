from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    course_id: int = Field(gt=0)

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=30,
    )

    semester: int = Field(
        gt=0,
        le=20,
    )

    credits: int = Field(
        gt=0,
        le=20,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class SubjectUpdate(BaseModel):
    course_id: int = Field(gt=0)

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=30,
    )

    semester: int = Field(
        gt=0,
        le=20,
    )

    credits: int = Field(
        gt=0,
        le=20,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_active: bool = True


class SubjectResponse(BaseModel):
    id: int
    course_id: int
    name: str
    code: str
    semester: int
    credits: int
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )