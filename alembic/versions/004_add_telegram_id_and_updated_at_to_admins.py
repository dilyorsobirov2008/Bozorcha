"""Add telegram_id and updated_at to admins table safely

Revision ID: 004
Revises: 003
Create Date: 2026-05-29 22:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('admins')]
    
    if 'telegram_id' not in columns:
        op.add_column('admins', sa.Column('telegram_id', sa.BigInteger(), nullable=True))
        op.create_index('ix_admins_telegram_id', 'admins', ['telegram_id'], unique=True)
        
    if 'updated_at' not in columns:
        op.add_column('admins', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('admins')]
    
    if 'telegram_id' in columns:
        op.drop_index('ix_admins_telegram_id', table_name='admins')
        op.drop_column('admins', 'telegram_id')
        
    if 'updated_at' in columns:
        op.drop_column('admins', 'updated_at')
