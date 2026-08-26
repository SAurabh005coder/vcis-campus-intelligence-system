from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=20,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class DepartmentUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    code: str = Field(
        min_length=2,
        max_length=20,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_active: bool = True


class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )