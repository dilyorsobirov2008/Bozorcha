"""Add created_at to users table safely

Revision ID: 003
Revises: 002
Create Date: 2026-05-29 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'created_at' not in columns:
        op.add_column('users', sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'created_at' in columns:
        op.drop_column('users', 'created_at')
