"""Drop unused login column from admins table safely

Revision ID: 006
Revises: 005
Create Date: 2026-05-29 22:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('admins')]
    
    if 'login' in columns:
        op.drop_column('admins', 'login')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('admins')]
    
    if 'login' not in columns:
        op.add_column('admins', sa.Column('login', sa.String(length=100), nullable=True))
