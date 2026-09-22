import os
from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def get_jwt_secret_key() -> str:
    """
    Retrieve the configured JWT secret key from the environment.
    Fails safely with a RuntimeError if not set, preventing any silent fallback.
    """
    secret_key = os.getenv("JWT_SECRET_KEY")
    if not secret_key or not secret_key.strip():
        raise RuntimeError("JWT_SECRET_KEY environment variable is not configured.")
    return secret_key.strip()


def get_jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256").strip()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        password,
        hashed_password,
    )