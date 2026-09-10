"""add foreign key from product.category_id to category.id

Revision ID: 12_add_product_category_fk
Revises: 11_add_product_fields
Create Date: 2026-06-30 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '12_add_product_category_fk'
down_revision: Union[str, Sequence[str], None] = '11_add_product_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        'fk_product_category',
        'Product',
        'category',
        ['category_id'],
        ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_product_category', 'Product', type_='foreignkey')
