"""create course and subject proposals tables

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-09-23 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to create course_proposals and subject_proposals tables and proposalstatus enum."""
    op.create_table(
        'course_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('proposed_by', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_years', sa.Integer(), nullable=False),
        sa.Column('total_semesters', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', name='proposalstatus'),
            nullable=False,
            server_default='PENDING_APPROVAL',
        ),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['proposed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_course_proposals_id'), 'course_proposals', ['id'], unique=False)
    op.create_index(op.f('ix_course_proposals_department_id'), 'course_proposals', ['department_id'], unique=False)
    op.create_index(op.f('ix_course_proposals_proposed_by'), 'course_proposals', ['proposed_by'], unique=False)
    op.create_index(op.f('ix_course_proposals_code'), 'course_proposals', ['code'], unique=False)

    op.create_table(
        'subject_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('proposed_by', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', name='proposalstatus', create_type=False),
            nullable=False,
            server_default='PENDING_APPROVAL',
        ),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id']),
        sa.ForeignKeyConstraint(['proposed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(op.f('ix_subject_proposals_id'), 'subject_proposals', ['id'], unique=False)
    op.create_index(op.f('ix_subject_proposals_course_id'), 'subject_proposals', ['course_id'], unique=False)
    op.create_index(op.f('ix_subject_proposals_proposed_by'), 'subject_proposals', ['proposed_by'], unique=False)
    op.create_index(op.f('ix_subject_proposals_code'), 'subject_proposals', ['code'], unique=False)


def downgrade() -> None:
    """Downgrade schema to drop course_proposals, subject_proposals, and proposalstatus enum."""
    op.drop_index(op.f('ix_subject_proposals_code'), table_name='subject_proposals')
    op.drop_index(op.f('ix_subject_proposals_proposed_by'), table_name='subject_proposals')
    op.drop_index(op.f('ix_subject_proposals_course_id'), table_name='subject_proposals')
    op.drop_index(op.f('ix_subject_proposals_id'), table_name='subject_proposals')
    op.drop_table('subject_proposals')

    op.drop_index(op.f('ix_course_proposals_code'), table_name='course_proposals')
    op.drop_index(op.f('ix_course_proposals_proposed_by'), table_name='course_proposals')
    op.drop_index(op.f('ix_course_proposals_department_id'), table_name='course_proposals')
    op.drop_index(op.f('ix_course_proposals_id'), table_name='course_proposals')
    op.drop_table('course_proposals')

    sa.Enum(name='proposalstatus').drop(op.get_bind(), checkfirst=True)
