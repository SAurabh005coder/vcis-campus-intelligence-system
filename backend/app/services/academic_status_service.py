"""
VCIS 3.0 — AI-Powered Campus Intelligence System
Academic Status Classification Service

This module is a pure, deterministic business-logic layer that converts
a predicted final semester score into an academic status tier:
- NORMAL (>= 60)
- MONITOR (50 <= score < 60)
- INTERVENTION (< 50)

Key Architecture Rules:
- Status is determined strictly from predicted_final_semester_score alone.
- Does not round or clamp the score prior to evaluation.
- Pure business logic: zero database, FastAPI, or ML framework dependencies.
- Rejects non-numeric, boolean, NaN, and infinite inputs cleanly.
"""

from enum import Enum
import math
from typing import Any


class AcademicStatus(str, Enum):
    """Enumeration of academic status classifications in VCIS 3.0."""
    NORMAL = "NORMAL"
    MONITOR = "MONITOR"
    INTERVENTION = "INTERVENTION"


class AcademicStatusError(Exception):
    """Base exception for academic status classification errors."""


class InvalidScoreError(AcademicStatusError, ValueError):
    """Raised when the predicted score is non-numeric, boolean, NaN, or non-finite."""


# Exact frozen thresholds
NORMAL_THRESHOLD = 60.0
MONITOR_THRESHOLD = 50.0


def get_academic_status(predicted_final_semester_score: Any) -> AcademicStatus:
    """
    Classify a predicted final semester score into an AcademicStatus.

    Business Rules:
    - NORMAL: predicted_final_semester_score >= 60.0
    - MONITOR: 50.0 <= predicted_final_semester_score < 60.0
    - INTERVENTION: predicted_final_semester_score < 50.0

    Args:
        predicted_final_semester_score: Numeric predicted score (int or float).

    Returns:
        AcademicStatus: The corresponding AcademicStatus enum member.

    Raises:
        InvalidScoreError: If input is not a numeric type, is a boolean, is NaN, or is infinite.
    """
    # Reject booleans (since in Python bool subclasses int)
    if isinstance(predicted_final_semester_score, bool):
        raise InvalidScoreError(
            f"Invalid score type: boolean ({predicted_final_semester_score!r}) is not permitted."
        )

    # Reject non-numeric types
    if not isinstance(predicted_final_semester_score, (int, float)):
        raise InvalidScoreError(
            f"Invalid score type: expected int or float, got {type(predicted_final_semester_score).__name__}."
        )

    # Reject non-finite values (NaN, +inf, -inf)
    if not math.isfinite(predicted_final_semester_score):
        raise InvalidScoreError(
            f"Invalid score value: score must be finite, got {predicted_final_semester_score!r}."
        )

    score = float(predicted_final_semester_score)

    if score >= NORMAL_THRESHOLD:
        return AcademicStatus.NORMAL
    elif score >= MONITOR_THRESHOLD:
        return AcademicStatus.MONITOR
    else:
        return AcademicStatus.INTERVENTION
