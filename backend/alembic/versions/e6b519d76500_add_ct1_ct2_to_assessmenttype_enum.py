"""add_ct1_ct2_to_assessmenttype_enum

Revision ID: e6b519d76500
Revises: 5ef3d75a843a
Create Date: 2026-09-18 12:10:26.151685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6b519d76500'
down_revision: Union[str, Sequence[str], None] = '5ef3d75a843a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add CT1 and CT2 values to the PostgreSQL assessmenttype enum.

    Uses autocommit_block to ensure compatibility with PostgreSQL requirement
    that ALTER TYPE ... ADD VALUE cannot be executed inside a standard transaction block.
    Uses IF NOT EXISTS to ensure safe, idempotent execution.
    Existing records and values (INTERNAL, ASSIGNMENT, MIDTERM, FINAL) are preserved.
    """
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE assessmenttype ADD VALUE IF NOT EXISTS 'CT1'")
        op.execute("ALTER TYPE assessmenttype ADD VALUE IF NOT EXISTS 'CT2'")

    # Targeted data migration for known development record (id=1)
    op.execute(
        sa.text(
            """
            UPDATE assessments
            SET assessment_type = 'CT1'
            WHERE id = 1
              AND enrollment_id = 1
              AND assessment_type = 'INTERNAL'
              AND assessment_name = 'Internal Assessment 1'
              AND max_marks = 20
              AND obtained_marks = 16
            """
        )
    )


def downgrade() -> None:
    """
    Downgrade schema.

    Reverts the specific migrated development record (id=1) from 'CT1' back to 'INTERNAL'.
    Note: PostgreSQL does not natively support removing values from an existing enum type
    (e.g., there is no ALTER TYPE ... DROP VALUE). Removing enum values would require dropping
    and recreating the type and all referencing columns, which risks severe data loss or downtime.
    Therefore, the enum additions (CT1, CT2) are intentionally retained in the database type.
    """
    op.execute(
        sa.text(
            """
            UPDATE assessments
            SET assessment_type = 'INTERNAL'
            WHERE id = 1
              AND enrollment_id = 1
              AND assessment_type = 'CT1'
              AND assessment_name = 'Internal Assessment 1'
              AND max_marks = 20
              AND obtained_marks = 16
            """
        )
    )
