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

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")


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