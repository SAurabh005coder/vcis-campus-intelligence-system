"""
VCIS 3.0 — AI-Powered Campus Intelligence System
Prediction Schemas (Pydantic models for ML inference API)

Enforces:
- Target semester structural validation (semester >= 1)
- Structured prediction response with model metadata and feature dictionary
"""

from typing import Any
from pydantic import BaseModel, Field

from app.services.academic_status_service import AcademicStatus


class PredictionRequest(BaseModel):
    """Request schema for student final score prediction."""

    semester: int = Field(
        ...,
        ge=1,
        le=12,
        description="Target academic semester for prediction.",
        json_schema_extra={"example": 1},
    )


class PredictionResponse(BaseModel):
    """Response schema returned by the prediction endpoint."""

    student_id: int = Field(
        ...,
        description="Unique identifier of the student.",
        json_schema_extra={"example": 123},
    )
    semester: int = Field(
        ...,
        ge=1,
        le=12,
        description="Academic semester for which the prediction was computed.",
        json_schema_extra={"example": 1},
    )
    predicted_final_semester_score: float = Field(
        ...,
        description="Predicted final semester score, rounded to 2 decimal places.",
        json_schema_extra={"example": 88.48},
    )
    academic_status: AcademicStatus = Field(
        ...,
        description="Academic status classification (NORMAL, MONITOR, INTERVENTION).",
        json_schema_extra={"example": "NORMAL"},
    )
    model_version: str = Field(
        ...,
        description="Version of the pre-trained ML model artifact used.",
        json_schema_extra={"example": "1.0"},
    )
    model_type: str = Field(
        ...,
        description="Architecture of the ML model (e.g. LinearRegression).",
        json_schema_extra={"example": "LinearRegression"},
    )
    scenario: str = Field(
        ...,
        description="Scenario description of the model (e.g. 'Semester 1' or 'Semesters 2+').",
        json_schema_extra={"example": "Semester 1"},
    )
    features: dict[str, float] = Field(
        ...,
        description="Exact dictionary of database-extracted ML features used for inference.",
        json_schema_extra={
            "example": {
                "current_attendance": 80.0,
                "current_assignment_average": 90.0,
                "current_ct1_average": 85.0,
            }
        },
    )
