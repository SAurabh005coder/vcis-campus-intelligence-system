from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.attendance import AttendanceStatus


class AttendanceCreate(BaseModel):
    enrollment_id: int = Field(gt=0)

    attendance_date: date

    status: AttendanceStatus

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus

    remarks: str | None = Field(
        default=None,
        max_length=1000,
    )


class AttendanceResponse(BaseModel):
    id: int
    enrollment_id: int
    attendance_date: date
    status: AttendanceStatus
    remarks: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )