"""Create initial tables

Revision ID: 001_initial
Revises: 
Create Date: 2026-07-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create turns table
    op.create_table(
        'turns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('latency_ms', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('ix_turns_session_id', 'turns', ['session_id'])
    op.create_index('ix_turns_created_at', 'turns', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_turns_created_at', table_name='turns')
    op.drop_index('ix_turns_session_id', table_name='turns')
    op.drop_table('turns')
    op.drop_table('sessions')
