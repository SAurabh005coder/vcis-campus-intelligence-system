"""create interventions table

Revision ID: b28f74e91a03
Revises: e6b519d76500
Create Date: 2026-09-18 16:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b28f74e91a03'
down_revision: Union[str, Sequence[str], None] = 'e6b519d76500'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to create interventions table and associated enums."""
    op.create_table(
        'interventions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('faculty_id', sa.Integer(), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column(
            'intervention_type',
            sa.Enum(
                'EXTRA_CLASS',
                'ADDITIONAL_ASSIGNMENT',
                'COUNSELLING',
                'MONITORING',
                name='interventiontype',
            ),
            nullable=False,
        ),
        sa.Column(
            'status',
            sa.Enum(
                'ASSIGNED',
                'IN_PROGRESS',
                'COMPLETED',
                'DISMISSED',
                name='interventionstatus',
            ),
            nullable=False,
            server_default='ASSIGNED',
        ),
        sa.Column('trigger_predicted_score', sa.Float(), nullable=False),
        sa.Column(
            'trigger_academic_status',
            sa.Enum(
                'NORMAL',
                'MONITOR',
                'INTERVENTION',
                name='academicstatus',
            ),
            nullable=False,
        ),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('action_plan', sa.Text(), nullable=True),
        sa.Column('follow_up_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['faculty_id'], ['faculty.id']),
        sa.CheckConstraint('semester >= 1 AND semester <= 4', name='check_intervention_semester_range'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_interventions_id'), 'interventions', ['id'], unique=False)
    op.create_index(op.f('ix_interventions_student_id'), 'interventions', ['student_id'], unique=False)
    op.create_index(op.f('ix_interventions_faculty_id'), 'interventions', ['faculty_id'], unique=False)
    op.create_index(op.f('ix_interventions_semester'), 'interventions', ['semester'], unique=False)
    op.create_index(op.f('ix_interventions_intervention_type'), 'interventions', ['intervention_type'], unique=False)
    op.create_index(op.f('ix_interventions_status'), 'interventions', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema to remove interventions table and enums."""
    op.drop_index(op.f('ix_interventions_status'), table_name='interventions')
    op.drop_index(op.f('ix_interventions_intervention_type'), table_name='interventions')
    op.drop_index(op.f('ix_interventions_semester'), table_name='interventions')
    op.drop_index(op.f('ix_interventions_faculty_id'), table_name='interventions')
    op.drop_index(op.f('ix_interventions_student_id'), table_name='interventions')
    op.drop_index(op.f('ix_interventions_id'), table_name='interventions')
    op.drop_table('interventions')

    # Drop the created PostgreSQL enums
    sa.Enum(name='interventiontype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='interventionstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='academicstatus').drop(op.get_bind(), checkfirst=True)
