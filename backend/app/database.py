import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Resolve backend directory relative to this file: backend/app/database.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parent.parent
env_path = BACKEND_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

def normalize_database_url(url: str) -> str:
    """
    Ensure standard PostgreSQL connection strings work with the installed psycopg 3 package.
    Converts 'postgres://' or 'postgresql://' to 'postgresql+psycopg://'.
    Preserves explicit driver specifications (e.g. 'postgresql+psycopg://') and sqlite.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

DATABASE_URL = normalize_database_url(DATABASE_URL)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)




def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()