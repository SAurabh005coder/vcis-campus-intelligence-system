from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreate(BaseModel):
    user_id: int = Field(gt=0)
    department_id: int = Field(gt=0)
    course_id: int = Field(gt=0)

    roll_number: str = Field(
        min_length=3,
        max_length=30,
    )

    admission_year: int = Field(
        ge=2000,
        le=2100,
    )

    current_semester: int = Field(
        ge=1,
        le=20,
    )

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr


class StudentUpdate(BaseModel):
    department_id: int = Field(gt=0)
    course_id: int = Field(gt=0)

    roll_number: str = Field(
        min_length=3,
        max_length=30,
    )

    admission_year: int = Field(
        ge=2000,
        le=2100,
    )

    current_semester: int = Field(
        ge=1,
        le=20,
    )

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    is_active: bool = True


class StudentResponse(BaseModel):
    id: int
    user_id: int
    department_id: int
    course_id: int
    roll_number: str
    admission_year: int
    current_semester: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)