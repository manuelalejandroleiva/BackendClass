"""add precio_wash and cantidad_lavados to tables

Revision ID: 5ac5b7557f7c
Revises: 07_add_tipo_mesa
Create Date: 2026-06-07 12:50:34.123796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ac5b7557f7c'
down_revision: Union[str, Sequence[str], None] = '07_add_tipo_mesa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('Tables', sa.Column('precio_wash', sa.Integer(), nullable=True))
    op.add_column('Tables', sa.Column('cantidad_lavados', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('Tables', 'cantidad_lavados')
    op.drop_column('Tables', 'precio_wash')
