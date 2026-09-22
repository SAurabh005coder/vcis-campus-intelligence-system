"""extend students academic profile

Revision ID: 9a0b9ad7329b
Revises: eed25aa6fde4
Create Date: 2026-08-27

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a0b9ad7329b"
down_revision: Union[str, Sequence[str], None] = "eed25aa6fde4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ---------------------------------------------------------
    # 1. Add new Student columns temporarily nullable.
    # ---------------------------------------------------------

    op.add_column(
        "students",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.add_column(
        "students",
        sa.Column("department_id", sa.Integer(), nullable=True),
    )

    op.add_column(
        "students",
        sa.Column("course_id", sa.Integer(), nullable=True),
    )

    op.add_column(
        "students",
        sa.Column("roll_number", sa.String(length=30), nullable=True),
    )

    op.add_column(
        "students",
        sa.Column("admission_year", sa.Integer(), nullable=True),
    )

    op.add_column(
        "students",
        sa.Column("current_semester", sa.Integer(), nullable=True),
    )

    op.add_column(
        "students",
        sa.Column("is_active", sa.Boolean(), nullable=True),
    )

    op.add_column(
        "students",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "students",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # ---------------------------------------------------------
    # 2. Create User accounts for legacy Students.
    # ---------------------------------------------------------

    now = sa.func.now()

    # Student #1 already belongs to User #1.
    #
    # Create users for the remaining five legacy students.
    op.execute(
        sa.text(
            """
            INSERT INTO users (
                email,
                password_hash,
                role,
                is_active,
                created_at,
                updated_at
            )
            SELECT
                s.email,
                'LEGACY_PASSWORD_RESET_REQUIRED',
                'STUDENT',
                TRUE,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            FROM students s
            WHERE s.id IN (3, 7, 8, 10, 11)
            AND NOT EXISTS (
                SELECT 1
                FROM users u
                WHERE u.email = s.email
            )
            """
        )
    )

    # ---------------------------------------------------------
    # 3. Populate Student academic data.
    # ---------------------------------------------------------

    op.execute(
        sa.text(
            """
            UPDATE students
            SET
                user_id = (
                    SELECT u.id
                    FROM users u
                    WHERE u.email = students.email
                ),
                department_id = 4,
                course_id = 2,
                roll_number = CASE id
                    WHEN 1 THEN 'MCA2026001'
                    WHEN 3 THEN 'MCA2026002'
                    WHEN 7 THEN 'MCA2026003'
                    WHEN 8 THEN 'MCA2026004'
                    WHEN 10 THEN 'MCA2026005'
                    WHEN 11 THEN 'MCA2026006'
                END,
                admission_year = 2026,
                current_semester = 3,
                is_active = TRUE,
                created_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            """
        )
    )

    # ---------------------------------------------------------
    # 4. Verify that every Student was populated.
    # ---------------------------------------------------------

    connection = op.get_bind()

    missing_count = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM students
            WHERE
                user_id IS NULL
                OR department_id IS NULL
                OR course_id IS NULL
                OR roll_number IS NULL
                OR admission_year IS NULL
                OR current_semester IS NULL
                OR is_active IS NULL
                OR created_at IS NULL
                OR updated_at IS NULL
            """
        )
    ).scalar_one()

    if missing_count != 0:
        raise RuntimeError(
            f"Student migration failed: "
            f"{missing_count} records were not populated."
        )

    # ---------------------------------------------------------
    # 5. Add foreign keys.
    # ---------------------------------------------------------

    op.create_foreign_key(
        "fk_students_user_id_users",
        "students",
        "users",
        ["user_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_students_department_id_departments",
        "students",
        "departments",
        ["department_id"],
        ["id"],
    )

    op.create_foreign_key(
        "fk_students_course_id_courses",
        "students",
        "courses",
        ["course_id"],
        ["id"],
    )

    # ---------------------------------------------------------
    # 6. Add indexes.
    # ---------------------------------------------------------

    op.create_index(
        "ix_students_user_id",
        "students",
        ["user_id"],
        unique=True,
    )

    op.create_index(
        "ix_students_department_id",
        "students",
        ["department_id"],
        unique=False,
    )

    op.create_index(
        "ix_students_course_id",
        "students",
        ["course_id"],
        unique=False,
    )

    op.create_index(
        "ix_students_roll_number",
        "students",
        ["roll_number"],
        unique=True,
    )

    # ---------------------------------------------------------
    # 7. Convert populated columns to NOT NULL.
    # ---------------------------------------------------------

    op.alter_column(
        "students",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "students",
        "department_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "students",
        "course_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "students",
        "roll_number",
        existing_type=sa.String(length=30),
        nullable=False,
    )

    op.alter_column(
        "students",
        "admission_year",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "students",
        "current_semester",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.alter_column(
        "students",
        "is_active",
        existing_type=sa.Boolean(),
        nullable=False,
    )

    op.alter_column(
        "students",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )

    op.alter_column(
        "students",
        "updated_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_students_roll_number",
        table_name="students",
    )

    op.drop_index(
        "ix_students_course_id",
        table_name="students",
    )

    op.drop_index(
        "ix_students_department_id",
        table_name="students",
    )

    op.drop_index(
        "ix_students_user_id",
        table_name="students",
    )

    op.drop_constraint(
        "fk_students_course_id_courses",
        "students",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_students_department_id_departments",
        "students",
        type_="foreignkey",
    )

    op.drop_constraint(
        "fk_students_user_id_users",
        "students",
        type_="foreignkey",
    )

    op.drop_column("students", "updated_at")
    op.drop_column("students", "created_at")
    op.drop_column("students", "is_active")
    op.drop_column("students", "current_semester")
    op.drop_column("students", "admission_year")
    op.drop_column("students", "roll_number")
    op.drop_column("students", "course_id")
    op.drop_column("students", "department_id")
    op.drop_column("students", "user_id")