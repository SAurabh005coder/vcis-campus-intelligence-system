import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    get_jwt_algorithm,
    get_jwt_secret_key,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == login_data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
        )

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    secret_key = get_jwt_secret_key()
    algorithm = get_jwt_algorithm()
    expires_minutes = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes
    )

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "exp": expires_at,
    }

    access_token = jwt.encode(
        payload,
        secret_key,
        algorithm=algorithm,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )