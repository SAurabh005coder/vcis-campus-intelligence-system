"""generalize intervention semester range to support multi-program durations

Revision ID: c3d4e5f6a1b2
Revises: b28f74e91a03
Create Date: 2026-09-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a1b2'
down_revision: Union[str, Sequence[str], None] = 'b28f74e91a03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema to generalize the intervention semester range check constraint
    from 1..4 to 1..12, allowing variable academic program durations (such as B.Tech 8 semesters).
    """
    op.drop_constraint('check_intervention_semester_range', 'interventions', type_='check')
    op.create_check_constraint(
        'check_intervention_semester_range',
        'interventions',
        'semester >= 1 AND semester <= 12',
    )


def downgrade() -> None:
    """
    Downgrade schema to restore the original 4-semester check constraint on interventions.
    """
    op.drop_constraint('check_intervention_semester_range', 'interventions', type_='check')
    op.create_check_constraint(
        'check_intervention_semester_range',
        'interventions',
        'semester >= 1 AND semester <= 4',
    )
