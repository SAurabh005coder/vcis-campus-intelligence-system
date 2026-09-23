import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.database import engine
from app.routers.assessments import router as assessments_router
from app.routers.attendance import router as attendance_router
from app.routers.auth import router as auth_router
from app.routers.courses import router as courses_router
from app.routers.departments import router as departments_router
from app.routers.enrollments import router as enrollment_router
from app.routers.faculty import router as faculty_router
from app.routers.interventions import router as interventions_router
from app.routers.predictions import router as predictions_router
from app.routers.results import router as results_router
from app.routers.students import router as students_router
from app.routers.subjects import router as subjects_router
from app.routers.users import router as users_router
from app.routers.course_proposals import router as course_proposals_router
from app.routers.subject_proposals import router as subject_proposals_router

logger = logging.getLogger(__name__)


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
    origins = [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip() and origin.strip() != "*"
    ]
    return origins if origins else ["http://localhost:5173"]


app = FastAPI(title="VCIS — Virtual Campus Intelligence System")
app.include_router(students_router)
app.include_router(enrollment_router)
app.include_router(departments_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(faculty_router)
app.include_router(courses_router)
app.include_router(subjects_router)
app.include_router(attendance_router)
app.include_router(assessments_router)
app.include_router(results_router)
app.include_router(predictions_router)
app.include_router(interventions_router)
app.include_router(course_proposals_router)
app.include_router(subject_proposals_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        logger.error("Database health check failed: %s", error, exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "detail": "Database connection error",
            },
        )