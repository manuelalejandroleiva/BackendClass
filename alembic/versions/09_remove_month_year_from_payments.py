"""remove month and year from payments

Revision ID: 09_remove_month_year
Revises: 08_add_landlord_tables
Create Date: 2026-06-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '09_remove_month_year'
down_revision: Union[str, Sequence[str], None] = '08_add_landlord_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('payments', 'month')
    op.drop_column('payments', 'year')


def downgrade() -> None:
    op.add_column('payments', sa.Column('month', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('payments', sa.Column('year', sa.Integer(), nullable=False, server_default='2026'))
    op.alter_column('payments', 'month', server_default=None)
    op.alter_column('payments', 'year', server_default=None)
