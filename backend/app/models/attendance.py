from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"


class Attendance(Base):
    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint(
            "enrollment_id",
            "attendance_date",
            name="uq_attendance_enrollment_date",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id"),
        nullable=False,
        index=True,
    )

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        SQLEnum(AttendanceStatus),
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )