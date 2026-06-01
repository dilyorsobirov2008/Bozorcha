"""Heal admins table by adding any remaining missing columns safely

Revision ID: 005
Revises: 004
Create Date: 2026-05-29 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('admins')]
    
    if 'username' not in columns:
        op.add_column('admins', sa.Column('username', sa.String(length=100), nullable=True))
        op.create_index('ix_admins_username', 'admins', ['username'], unique=True)
        
    if 'password_hash' not in columns:
        op.add_column('admins', sa.Column('password_hash', sa.String(length=255), nullable=True))
        
    if 'is_active' not in columns:
        op.add_column('admins', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
        
    if 'created_at' not in columns:
        op.add_column('admins', sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('admins')]
    
    if 'username' in columns:
        op.drop_index('ix_admins_username', table_name='admins')
        op.drop_column('admins', 'username')
        
    if 'password_hash' in columns:
        op.drop_column('admins', 'password_hash')
        
    if 'is_active' in columns:
        op.drop_column('admins', 'is_active')
        
    if 'created_at' in columns:
        op.drop_column('admins', 'created_at')
