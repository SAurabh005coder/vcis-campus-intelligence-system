from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.faculty import Faculty
from app.models.user import User, UserRole


def require_roles(*allowed_roles: UserRole) -> Callable:
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return role_checker


def resolve_hod_department_id(user: User, db: Session) -> int:
    """
    Resolve the department ID for an authenticated HOD user.

    Enforces that:
    1. The user has the HOD role.
    2. The user has an associated Faculty record where Faculty.user_id == user.id.
    3. The Faculty record contains a valid department_id.

    Fails safely with HTTP 403 Forbidden if any condition is not met.
    """
    if user.role != UserRole.HOD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not authorized as a Head of Department.",
        )

    faculty = (
        db.query(Faculty)
        .filter(Faculty.user_id == user.id)
        .first()
    )

    if faculty is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HOD does not have an associated faculty profile.",
        )

    if faculty.department_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HOD faculty profile has no assigned department.",
        )

    return faculty.department_id


def get_current_hod_department(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int:
    """
    FastAPI dependency that resolves the department ID for the authenticated HOD.
    """
    return resolve_hod_department_id(current_user, db)