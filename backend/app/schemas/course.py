from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    department_id: int = Field(gt=0)

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=30,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    duration_years: int = Field(
        gt=0,
        le=10,
    )

    total_semesters: int = Field(
        gt=0,
        le=20,
    )


class CourseUpdate(BaseModel):
    department_id: int = Field(gt=0)

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=30,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    duration_years: int = Field(
        gt=0,
        le=10,
    )

    total_semesters: int = Field(
        gt=0,
        le=20,
    )

    is_active: bool = True


class CourseResponse(BaseModel):
    id: int
    department_id: int
    name: str
    code: str
    description: str | None
    duration_years: int
    total_semesters: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )