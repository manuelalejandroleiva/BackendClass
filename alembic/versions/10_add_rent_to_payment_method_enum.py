"""add 'rent' to paymentmethod enum

Revision ID: 10_add_rent_payment_method
Revises: 09_remove_month_year
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '10_add_rent_payment_method'
down_revision: Union[str, Sequence[str], None] = '09_remove_month_year'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'rent'")


def downgrade() -> None:
    # Cannot remove a value from an enum in PostgreSQL without recreating the type.
    # In practice, a downgrade would require creating a new type without 'rent',
    # altering all columns, and dropping the old type. This is left as a manual
    # operation if needed.
    pass
