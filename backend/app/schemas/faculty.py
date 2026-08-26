
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FacultyCreate(BaseModel):
    user_id: int = Field(gt=0)

    department_id: int = Field(gt=0)

    employee_code: str = Field(
        min_length=2,
        max_length=30,
    )

    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    designation: str = Field(
        min_length=2,
        max_length=100,
    )

    phone: str | None = Field(
        default=None,
        max_length=20,
    )


class FacultyUpdate(BaseModel):
    department_id: int = Field(gt=0)

    employee_code: str = Field(
        min_length=2,
        max_length=30,
    )

    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    designation: str = Field(
        min_length=2,
        max_length=100,
    )

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    is_active: bool = True


class FacultyResponse(BaseModel):
    id: int
    user_id: int
    department_id: int
    employee_code: str
    first_name: str
    last_name: str
    designation: str
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )