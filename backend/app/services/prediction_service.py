"""
VCIS 3.0 — AI-Powered Campus Intelligence System
Prediction Service (Machine Learning Inference Layer)

This module is responsible ONLY for loading the pre-trained VCIS regression model
artifacts and generating predictions from explicitly supplied, pre-computed feature values.

Key Architecture Constraints:
- No database queries or SQLAlchemy dependencies.
- No HTTP or FastAPI dependencies.
- No pandas dependency.
- Validates numeric and finite feature values.
- Respects the feature order stored in each artifact.
- Does not modify, round, or clamp model output scores.
"""

from collections.abc import Mapping, Sequence
import math
import os
from pathlib import Path
from typing import Any
import warnings

import joblib


# =====================================================================
# CUSTOM EXCEPTIONS
# =====================================================================

class PredictionServiceError(Exception):
    """Base exception for prediction service errors."""


class ModelArtifactNotFoundError(PredictionServiceError, FileNotFoundError):
    """Raised when a required model artifact file cannot be located on disk."""


class ModelLoadingError(PredictionServiceError, RuntimeError):
    """Raised when a model artifact exists but fails to load or has an invalid structure."""


class UnsupportedSemesterError(PredictionServiceError, ValueError):
    """Raised when prediction is requested for an unsupported semester."""


class InvalidFeatureError(PredictionServiceError, ValueError):
    """Raised when supplied features are missing, unexpected, non-numeric, or non-finite."""


# =====================================================================
# CONFIGURATION & ARTIFACT RESOLUTION
# =====================================================================

# Backward compatibility mapping for semesters 1-4
SEMESTER_MODEL_MAP: dict[int, str] = {
    1: "vcis_model_semester1.joblib",
    2: "vcis_model_semesters2_4.joblib",
    3: "vcis_model_semesters2_4.joblib",
    4: "vcis_model_semesters2_4.joblib",
}

# Module-level singleton cache for loaded model artifacts
_MODEL_CACHE: dict[str, dict[str, Any]] = {}


def resolve_models_directory() -> Path:
    """
    Resolve the absolute directory containing the model artifacts.

    Priority:
    1. VCIS_MODELS_DIR environment variable if configured and valid.
    2. Project root 'vcis_models/' (4 levels up from this file).
    3. Backend-local 'backend/vcis_models/' (3 levels up from this file).

    Returns:
        Path: Absolute path to the resolved models directory.
    """
    env_dir = os.getenv("VCIS_MODELS_DIR")
    if env_dir:
        env_path = Path(env_dir).resolve()
        if env_path.is_dir():
            return env_path

    # Current file: <project_root>/backend/app/services/prediction_service.py
    project_root = Path(__file__).resolve().parents[3]
    root_candidate = project_root / "vcis_models"
    if root_candidate.is_dir():
        return root_candidate

    backend_candidate = Path(__file__).resolve().parents[2] / "vcis_models"
    if backend_candidate.is_dir():
        return backend_candidate

    # Return default root candidate path even if not yet created (for clear error messaging)
    return root_candidate


def get_model_artifact_path(semester: int) -> Path:
    """
    Return the expected file path for the model artifact of a given semester.

    Conceptual routing:
    - semester == 1 -> Model 1 (vcis_model_semester1.joblib)
    - semester >= 2 -> Model 2 (vcis_model_semesters2_4.joblib)

    Args:
        semester: Academic semester (>= 1).

    Returns:
        Path: Absolute path to the model artifact.

    Raises:
        UnsupportedSemesterError: If semester < 1.
    """
    if semester < 1:
        raise UnsupportedSemesterError(
            f"Semester {semester} is not supported. Semester must be >= 1."
        )

    filename = "vcis_model_semester1.joblib" if semester == 1 else "vcis_model_semesters2_4.joblib"
    models_dir = resolve_models_directory()
    return models_dir / filename


# =====================================================================
# ARTIFACT LOADING & CACHING
# =====================================================================

def load_model_artifact(semester: int) -> dict[str, Any]:
    """
    Load and cache the trained model artifact for the given semester.

    Uses module-level lazy loading so each artifact is read from disk
    only once during application runtime.

    Args:
        semester: Academic semester (>= 1).

    Returns:
        dict: The loaded artifact dictionary containing:
            - 'model': Trained regression model object
            - 'features': Sequence of feature names
            - 'target': Target variable name ('final_semester_score')
            - 'model_type': Type of model ('LinearRegression')
            - 'scenario': Scenario description
            - 'version': Model version string

    Raises:
        UnsupportedSemesterError: If semester is invalid.
        ModelArtifactNotFoundError: If the .joblib file does not exist.
        ModelLoadingError: If loading fails or artifact structure is invalid.
    """
    artifact_path = get_model_artifact_path(semester)
    cache_key = str(artifact_path.resolve())

    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    if not artifact_path.is_file():
        raise ModelArtifactNotFoundError(
            f"Model artifact not found at: '{artifact_path}'. "
            f"Please ensure the trained joblib model is present in the models directory."
        )

    try:
        artifact = joblib.load(artifact_path)
    except Exception as exc:
        raise ModelLoadingError(
            f"Failed to load model artifact from '{artifact_path}': {exc}"
        ) from exc

    if not isinstance(artifact, dict):
        raise ModelLoadingError(
            f"Expected artifact at '{artifact_path}' to be a dictionary, "
            f"got {type(artifact).__name__}."
        )

    required_keys = {"model", "features", "target", "model_type", "scenario", "version"}
    missing_keys = required_keys - set(artifact.keys())
    if missing_keys:
        raise ModelLoadingError(
            f"Artifact at '{artifact_path}' is missing required keys: {sorted(missing_keys)}."
        )

    model_obj = artifact.get("model")
    if not hasattr(model_obj, "predict") or not callable(getattr(model_obj, "predict")):
        raise ModelLoadingError(
            f"Loaded model object from '{artifact_path}' does not provide a callable 'predict' method."
        )

    features = artifact.get("features")
    if not isinstance(features, (list, tuple)) or len(features) == 0:
        raise ModelLoadingError(
            f"Loaded features from '{artifact_path}' must be a non-empty sequence of strings."
        )

    _MODEL_CACHE[cache_key] = artifact
    return artifact


def clear_model_cache() -> None:
    """Clear all cached model artifacts from memory."""
    _MODEL_CACHE.clear()


# =====================================================================
# METADATA EXTRACTION
# =====================================================================

def get_model_metadata(semester: int) -> dict[str, Any]:
    """
    Expose model metadata needed by API/service consumers without running inference.

    Args:
        semester: Academic semester (>= 1).

    Returns:
        dict: Metadata dictionary containing:
            - 'model_version': str
            - 'scenario': str
            - 'model_type': str
            - 'feature_names': list[str]
            - 'target_name': str
            - 'artifact_path': str
    """
    artifact = load_model_artifact(semester)
    artifact_path = get_model_artifact_path(semester)

    scenario = "Semester 1" if semester == 1 else "Semesters 2+"

    return {
        "model_version": str(artifact.get("version")),
        "scenario": scenario,
        "model_type": str(artifact.get("model_type")),
        "feature_names": list(artifact.get("features", [])),
        "target_name": str(artifact.get("target")),
        "artifact_path": str(artifact_path.resolve()),
    }


# =====================================================================
# FEATURE VALIDATION & VECTOR CONSTRUCTION
# =====================================================================

def validate_and_order_features(
    semester: int,
    features: Mapping[str, Any],
    expected_features: Sequence[str],
) -> list[float]:
    """
    Validate that feature inputs contain exactly the expected numeric keys
    with finite values, and return them ordered according to the artifact metadata.

    Args:
        semester: Target semester for error context.
        features: Mapping of feature names to values.
        expected_features: Ordered sequence of feature names expected by the model.

    Returns:
        list[float]: Feature values ordered strictly as required by the model.

    Raises:
        InvalidFeatureError: If keys are missing, unexpected, non-numeric, or non-finite.
    """
    if not isinstance(features, Mapping):
        raise InvalidFeatureError(
            f"Features must be supplied as a Mapping (e.g. dict), got {type(features).__name__}."
        )

    missing_keys = set(expected_features) - set(features.keys())
    if missing_keys:
        raise InvalidFeatureError(
            f"Missing required features for semester {semester}: {sorted(missing_keys)}."
        )

    unexpected_keys = set(features.keys()) - set(expected_features)
    if unexpected_keys:
        raise InvalidFeatureError(
            f"Unexpected features provided for semester {semester}: {sorted(unexpected_keys)}."
        )

    ordered_vector: list[float] = []
    for feature_name in expected_features:
        value = features.get(feature_name)

        if value is None:
            raise InvalidFeatureError(
                f"Feature '{feature_name}' for semester {semester} cannot be None."
            )

        if isinstance(value, bool):
            raise InvalidFeatureError(
                f"Feature '{feature_name}' for semester {semester} must be numeric, got boolean."
            )

        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError) as exc:
                raise InvalidFeatureError(
                    f"Feature '{feature_name}' for semester {semester} must be a valid numeric type."
                ) from exc

        if math.isnan(value) or math.isinf(value):
            raise InvalidFeatureError(
                f"Feature '{feature_name}' for semester {semester} contains non-finite value: {value}."
            )

        ordered_vector.append(float(value))

    return ordered_vector


# =====================================================================
# INFERENCE SERVICE API
# =====================================================================

def predict_final_score(
    semester: int,
    features: Mapping[str, Any],
) -> float:
    """
    Generate an early final semester score prediction for a given semester
    using pre-computed feature values.

    Args:
        semester: The target semester (>= 1).
        features: Mapping containing exactly the required features for that semester.

    Requirements enforced:
        - Semester 1 requires exactly:
            current_attendance, current_assignment_average, current_ct1_average
        - Semesters 2+ require exactly:
            previous_semester_score, previous_semester_attendance,
            current_attendance, current_assignment_average, current_ct1_average
        - Feature vector ordered strictly according to artifact metadata.
        - Returns raw predicted final semester score as a float without rounding or clamping.

    Returns:
        float: The raw predicted final semester score.

    Raises:
        UnsupportedSemesterError: If semester is less than 1.
        ModelArtifactNotFoundError: If the joblib model artifact is missing.
        ModelLoadingError: If loading the model artifact fails.
        InvalidFeatureError: If features do not match requirements or are non-finite.
    """
    if semester < 1:
        raise UnsupportedSemesterError(
            f"Semester {semester} is not supported. Semester must be >= 1."
        )

    artifact = load_model_artifact(semester)
    expected_features = artifact["features"]
    model = artifact["model"]

    ordered_vector = validate_and_order_features(
        semester=semester,
        features=features,
        expected_features=expected_features,
    )

    # Suppress scikit-learn UserWarning regarding 2D array feature names during inference
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        prediction = model.predict([ordered_vector])

    return float(prediction[0])


def predict_semester_1(
    current_attendance: float | int,
    current_assignment_average: float | int,
    current_ct1_average: float | int,
) -> float:
    """
    Convenience function to predict final score for Semester 1.

    Args:
        current_attendance: Attendance percentage in current semester (0-100).
        current_assignment_average: Assignment percentage average in current semester (0-100).
        current_ct1_average: Class Test 1 percentage average in current semester (0-100).

    Returns:
        float: Raw predicted final semester score.
    """
    return predict_final_score(
        semester=1,
        features={
            "current_attendance": current_attendance,
            "current_assignment_average": current_assignment_average,
            "current_ct1_average": current_ct1_average,
        },
    )


def predict_semesters_2_plus(
    semester: int,
    previous_semester_score: float | int,
    previous_semester_attendance: float | int,
    current_attendance: float | int,
    current_assignment_average: float | int,
    current_ct1_average: float | int,
) -> float:
    """
    Convenience function to predict final score for Semesters 2 and above (2, 3, 4, 5, 6, 7, 8, etc.).

    Args:
        semester: Semester index (>= 2).
        previous_semester_score: Overall percentage score in previous semester (0-100).
        previous_semester_attendance: Attendance percentage in previous semester (0-100).
        current_attendance: Attendance percentage in current semester (0-100).
        current_assignment_average: Assignment percentage average in current semester (0-100).
        current_ct1_average: Class Test 1 percentage average in current semester (0-100).

    Returns:
        float: Raw predicted final semester score.
    """
    if semester < 2:
        raise UnsupportedSemesterError(
            f"Semester {semester} is not supported for Model 2. Expected semester >= 2."
        )

    return predict_final_score(
        semester=semester,
        features={
            "previous_semester_score": previous_semester_score,
            "previous_semester_attendance": previous_semester_attendance,
            "current_attendance": current_attendance,
            "current_assignment_average": current_assignment_average,
            "current_ct1_average": current_ct1_average,
        },
    )


def predict_semesters_2_to_4(
    semester: int,
    previous_semester_score: float | int,
    previous_semester_attendance: float | int,
    current_attendance: float | int,
    current_assignment_average: float | int,
    current_ct1_average: float | int,
) -> float:
    """
    Backward-compatibility wrapper forwarding to predict_semesters_2_plus.
    """
    return predict_semesters_2_plus(
        semester=semester,
        previous_semester_score=previous_semester_score,
        previous_semester_attendance=previous_semester_attendance,
        current_attendance=current_attendance,
        current_assignment_average=current_assignment_average,
        current_ct1_average=current_ct1_average,
    )


# =====================================================================
# SERVICE CLASS INTERFACE
# =====================================================================

class PredictionService:
    """
    Class-based interface wrapper for VCIS ML inference service.
    Exposes static methods for metadata retrieval and prediction.
    """

    @staticmethod
    def get_metadata(semester: int) -> dict[str, Any]:
        """Return model metadata for a given semester."""
        return get_model_metadata(semester)

    @staticmethod
    def predict(semester: int, features: Mapping[str, Any]) -> float:
        """Generate prediction for a given semester using supplied features."""
        return predict_final_score(semester, features)

    @staticmethod
    def predict_semester_1(
        current_attendance: float | int,
        current_assignment_average: float | int,
        current_ct1_average: float | int,
    ) -> float:
        """Predict for Semester 1."""
        return predict_semester_1(
            current_attendance=current_attendance,
            current_assignment_average=current_assignment_average,
            current_ct1_average=current_ct1_average,
        )

    @staticmethod
    def predict_semesters_2_plus(
        semester: int,
        previous_semester_score: float | int,
        previous_semester_attendance: float | int,
        current_attendance: float | int,
        current_assignment_average: float | int,
        current_ct1_average: float | int,
    ) -> float:
        """Predict for Semesters 2+."""
        return predict_semesters_2_plus(
            semester=semester,
            previous_semester_score=previous_semester_score,
            previous_semester_attendance=previous_semester_attendance,
            current_attendance=current_attendance,
            current_assignment_average=current_assignment_average,
            current_ct1_average=current_ct1_average,
        )

    @staticmethod
    def predict_semesters_2_to_4(
        semester: int,
        previous_semester_score: float | int,
        previous_semester_attendance: float | int,
        current_attendance: float | int,
        current_assignment_average: float | int,
        current_ct1_average: float | int,
    ) -> float:
        """Predict for Semesters 2+ (compatibility wrapper for historical callers)."""
        return predict_semesters_2_plus(
            semester=semester,
            previous_semester_score=previous_semester_score,
            previous_semester_attendance=previous_semester_attendance,
            current_attendance=current_attendance,
            current_assignment_average=current_assignment_average,
            current_ct1_average=current_ct1_average,
        )
