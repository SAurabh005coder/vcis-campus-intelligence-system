from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import (
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


class AssessmentType(str, Enum):
    INTERNAL = "internal"
    ASSIGNMENT = "assignment"
    MIDTERM = "midterm"
    FINAL = "final"
    CT1 = "ct1"
    CT2 = "ct2"


class Assessment(Base):
    __tablename__ = "assessments"

    __table_args__ = (
        UniqueConstraint(
            "enrollment_id",
            "assessment_type",
            "assessment_name",
            name="uq_enrollment_assessment",
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

    assessment_type: Mapped[AssessmentType] = mapped_column(
        SQLEnum(AssessmentType),
        nullable=False,
        index=True,
    )

    assessment_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    max_marks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    obtained_marks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    assessment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
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