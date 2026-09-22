import os
from app.models.department import Department
from logging.config import fileConfig
from dotenv import load_dotenv
from app.models.faculty import Faculty
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from app.models.course import Course
from app.models.subject import Subject
from app.models.enrollment import Enrollment
from app.models.attendance import Attendance
from app.models.assessment import Assessment

from alembic import context

from app.base import Base
from app.models.student import Student
from app.models.user import User
from app.models.intervention import Intervention

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    connectable = engine_from_config(
        {"sqlalchemy.url": database_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()