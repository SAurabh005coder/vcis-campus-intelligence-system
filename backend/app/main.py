from app.routers.students import router as students_router
from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine

app = FastAPI()
app.include_router(students_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/health/database")
def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception as error:
        return {
            "status": "error",
            "database": "disconnected",
            "detail": str(error)
        }