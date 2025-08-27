"""Add user cooldown system columns

Revision ID: 7d80be6f0f6c
Revises: 3d9f27983e62
Create Date: 2025-07-06 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7d80be6f0f6c'
down_revision = '3d9f27983e62'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing cooldown system columns to users table"""
    # Add questions_used_current_cycle column
    op.add_column('users', sa.Column('questions_used_current_cycle', sa.Integer(), nullable=False, server_default='0'))
    
    # Add cycle_reset_time column
    op.add_column('users', sa.Column('cycle_reset_time', sa.DateTime(timezone=True), nullable=True))
    
    # Add last_question_time column
    op.add_column('users', sa.Column('last_question_time', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove cooldown system columns from users table"""
    op.drop_column('users', 'last_question_time')
    op.drop_column('users', 'cycle_reset_time') 
    op.drop_column('users', 'questions_used_current_cycle')
