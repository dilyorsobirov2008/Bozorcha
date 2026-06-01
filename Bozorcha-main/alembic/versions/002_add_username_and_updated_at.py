"""Add username and updated_at to users table

Revision ID: 002
Revises: 001
Create Date: 2026-05-29 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We will use raw DDL or safe Alembic commands to add columns.
    # To prevent errors if the columns already exist, we can inspect the table first.
    conn = op.get_bind()
    
    # Check if 'username' exists
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'username' not in columns:
        op.add_column('users', sa.Column('username', sa.String(length=255), nullable=True))
        
    if 'updated_at' not in columns:
        op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'username' in columns:
        op.drop_column('users', 'username')
        
    if 'updated_at' in columns:
        op.drop_column('users', 'updated_at')


