from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class EnrollmentStatus(str, Enum):
    ENROLLED = "enrolled"
    COMPLETED = "completed"
    DROPPED = "dropped"


class Enrollment(Base):
    __tablename__ = "enrollments"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "academic_year",
            name="uq_student_subject_academic_year",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
        index=True,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"),
        nullable=False,
        index=True,
    )

    academic_year: Mapped[str] = mapped_column(
        String(9),
        nullable=False,
        index=True,
    )

    enrollment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    status: Mapped[EnrollmentStatus] = mapped_column(
        SQLEnum(EnrollmentStatus),
        nullable=False,
        default=EnrollmentStatus.ENROLLED,
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