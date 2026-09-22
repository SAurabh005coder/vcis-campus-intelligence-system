"""
VCIS 3.0 — Academic Intervention Model

Represents an actual academic support action assigned by Faculty/HOD/Admin
to support an at-risk student in a specific academic semester.
"""

from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base
from app.services.academic_status_service import AcademicStatus


class InterventionType(str, Enum):
    """The four canonical academic intervention types supported by VCIS 3.0."""
    EXTRA_CLASS = "extra_class"
    ADDITIONAL_ASSIGNMENT = "additional_assignment"
    COUNSELLING = "counselling"
    MONITORING = "monitoring"


class InterventionStatus(str, Enum):
    """Lifecycle statuses for academic intervention workflow."""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class Intervention(Base):
    __tablename__ = "interventions"

    __table_args__ = (
        CheckConstraint(
            "semester >= 1 AND semester <= 12",
            name="check_intervention_semester_range",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("faculty.id"),
        nullable=False,
        index=True,
    )

    semester: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    intervention_type: Mapped[InterventionType] = mapped_column(
        SQLEnum(InterventionType),
        nullable=False,
        index=True,
    )

    status: Mapped[InterventionStatus] = mapped_column(
        SQLEnum(InterventionStatus),
        nullable=False,
        default=InterventionStatus.ASSIGNED,
        index=True,
    )

    trigger_predicted_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    trigger_academic_status: Mapped[AcademicStatus] = mapped_column(
        SQLEnum(AcademicStatus),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    action_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    follow_up_date: Mapped[date | None] = mapped_column(
        Date,
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
