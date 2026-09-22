"""
VCIS 3.0 — Academic Intervention Schemas (Pydantic models)

Enforces:
- Target semester structural validation (semester >= 1)
- Finite numeric validation for trigger predicted score (rejects NaN, +/-Inf, boolean)
- Direct usage of InterventionType, InterventionStatus, and AcademicStatus enums
- Protection of historical trigger evidence from arbitrary mutation during updates
"""

from datetime import date, datetime
import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.intervention import InterventionStatus, InterventionType
from app.services.academic_status_service import AcademicStatus


def validate_finite_score(v: Any) -> float:
    """Validate that value is a finite float and strictly not a boolean."""
    if isinstance(v, bool):
        raise ValueError("trigger_predicted_score cannot be a boolean.")
    if not isinstance(v, (int, float)):
        try:
            v = float(v)
        except (TypeError, ValueError):
            raise ValueError("trigger_predicted_score must be a numeric value.")
    if math.isnan(v) or math.isinf(v):
        raise ValueError("trigger_predicted_score must be a finite numeric value.")
    return float(v)


class InterventionCreate(BaseModel):
    """Schema for creating a new academic intervention."""

    student_id: int = Field(
        ...,
        gt=0,
        description="Unique identifier of the target student.",
    )
    faculty_id: int = Field(
        ...,
        gt=0,
        description="Unique identifier of the assigning/managing faculty member.",
    )
    semester: int = Field(
        ...,
        ge=1,
        le=12,
        description="Academic semester for which the intervention is assigned.",
    )
    intervention_type: InterventionType = Field(
        ...,
        description="Type of intervention (extra_class, additional_assignment, counselling, monitoring).",
    )
    status: InterventionStatus = Field(
        default=InterventionStatus.ASSIGNED,
        description="Initial lifecycle status of the intervention (defaults to assigned).",
    )
    trigger_predicted_score: float = Field(
        ...,
        description="Exact raw predicted score that triggered this intervention.",
    )
    trigger_academic_status: AcademicStatus = Field(
        ...,
        description="Exact academic status classification at the time of intervention.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Detailed contextual notes regarding the intervention need.",
    )
    action_plan: str | None = Field(
        default=None,
        max_length=2000,
        description="Specific remedial plan of action, tasks, or milestones.",
    )
    follow_up_date: date | None = Field(
        default=None,
        description="Scheduled date for reviewing progress or resolving the intervention.",
    )

    @field_validator("trigger_predicted_score", mode="before")
    @classmethod
    def check_score(cls, v: Any) -> float:
        return validate_finite_score(v)


class InterventionUpdate(BaseModel):
    """
    Schema for updating an existing academic intervention workflow.

    Note: Historical trigger evidence (trigger_predicted_score, trigger_academic_status)
    is intentionally excluded to prevent mutation of audit evidence.
    """

    status: InterventionStatus | None = Field(
        default=None,
        description="Updated lifecycle status (assigned, in_progress, completed, dismissed).",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Updated description notes.",
    )
    action_plan: str | None = Field(
        default=None,
        max_length=2000,
        description="Updated remedial action plan.",
    )
    follow_up_date: date | None = Field(
        default=None,
        description="Updated follow-up / review date.",
    )


class InterventionResponse(BaseModel):
    """Response schema exposing the complete intervention record."""

    id: int
    student_id: int
    faculty_id: int
    semester: int
    intervention_type: InterventionType
    status: InterventionStatus
    trigger_predicted_score: float
    trigger_academic_status: AcademicStatus
    description: str | None = None
    action_plan: str | None = None
    follow_up_date: date | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
