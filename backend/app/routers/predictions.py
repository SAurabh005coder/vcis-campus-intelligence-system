"""
VCIS 3.0 — AI-Powered Campus Intelligence System
Predictions Router (ML Inference API Layer)

Exposes the pre-trained VCIS early score prediction pipeline through FastAPI:
1. Validates student ID and requested academic semester.
2. Extracts student-semester features via feature_service.py.
3. Injects feature vector directly into prediction_service.py.
4. Returns predicted final score and model metadata.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.authorization import require_roles, resolve_hod_department_id
from app.database import get_db
from app.models.student import Student
from app.models.user import User, UserRole
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.feature_service import (
    extract_ml_features,
    StudentNotFoundError,
    InsufficientDataError,
    UnsupportedSemesterError as FeatureUnsupportedSemesterError,
    FeatureExtractionError,
)
from app.services.prediction_service import (
    predict_final_score,
    get_model_metadata,
    ModelArtifactNotFoundError,
    ModelLoadingError,
    UnsupportedSemesterError as PredUnsupportedSemesterError,
    InvalidFeatureError,
    PredictionServiceError,
)
from app.services.academic_status_service import get_academic_status


router = APIRouter(
    tags=["Predictions"],
)


@router.post(
    "/predictions/students/{student_id}",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict final semester score for a student",
    description=(
        "Extracts current database features for the target semester and computes "
        "the predicted final semester score using the trained VCIS regression model."
    ),
)
@router.post(
    "/api/v1/predictions/students/{student_id}",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict final semester score for a student (v1 alias)",
    include_in_schema=False,
)
def predict_student_score(
    student_id: int,
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.STUDENT,
            UserRole.FACULTY,
            UserRole.HOD,
            UserRole.ADMIN,
        )
    ),
) -> PredictionResponse:
    """
    Generate an early final semester score prediction for a student.

    - Receives student_id from URL path.
    - Receives target semester from request body.
    - Extracts required features via feature_service.py.
    - Generates prediction via prediction_service.py.
    - Returns rounded prediction along with model metadata and features.
    """
    if student_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student ID.",
        )

    # Student IDOR Ownership Protection
    if current_user.role == UserRole.STUDENT:
        student_record = (
            db.query(Student)
            .filter(Student.user_id == current_user.id)
            .first()
        )
        if student_record is None or student_record.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access predictions for this student.",
            )
    elif current_user.role == UserRole.HOD:
        hod_department_id = resolve_hod_department_id(current_user, db)
        student_record = (
            db.query(Student)
            .filter(Student.id == student_id)
            .first()
        )
        if student_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {student_id} was not found.",
            )
        if student_record.department_id != hod_department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access predictions for a student outside your department.",
            )

    semester = request.semester

    # 1. Feature Extraction Layer
    try:
        features = extract_ml_features(
            db=db,
            student_id=student_id,
            semester=semester,
        )
    except StudentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except InsufficientDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except FeatureUnsupportedSemesterError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except FeatureExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while extracting academic features.",
        ) from exc

    # 2. Model Inference Layer
    try:
        raw_prediction = predict_final_score(
            semester=semester,
            features=features,
        )
        metadata = get_model_metadata(semester)
    except ModelArtifactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model artifact is currently unavailable.",
        ) from exc
    except ModelLoadingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model failed to load.",
        ) from exc
    except (PredUnsupportedSemesterError, InvalidFeatureError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except PredictionServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during score prediction.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        ) from exc

    # 3. Academic Status Classification (uses RAW prediction before display rounding)
    try:
        academic_status = get_academic_status(raw_prediction)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while evaluating academic status.",
        ) from exc

    # 4. Serialization Layer: Round prediction for API display
    rounded_prediction = round(float(raw_prediction), 2)

    return PredictionResponse(
        student_id=student_id,
        semester=semester,
        predicted_final_semester_score=rounded_prediction,
        academic_status=academic_status,
        model_version=metadata["model_version"],
        model_type=metadata["model_type"],
        scenario=metadata["scenario"],
        features=features,
    )
