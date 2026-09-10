"""add product fields: sku, description, category_id, cost, min_stock, pz

Revision ID: 11_add_product_fields
Revises: 10_add_rent_payment_method
Create Date: 2026-06-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '11_add_product_fields'
down_revision: Union[str, Sequence[str], None] = '10_add_rent_payment_method'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('Product', sa.Column('sku', sa.String(), nullable=True, index=True))
    op.add_column('Product', sa.Column('description', sa.String(), nullable=True))
    op.add_column('Product', sa.Column('category_id', sa.Integer(), nullable=True, index=True))
    op.add_column('Product', sa.Column('cost', sa.Integer(), nullable=True, server_default=sa.text('0')))
    op.add_column('Product', sa.Column('min_stock', sa.Integer(), nullable=True, server_default=sa.text('0')))
    op.add_column('Product', sa.Column('pz', sa.Integer(), nullable=True, server_default=sa.text('1')))


def downgrade() -> None:
    op.drop_column('Product', 'pz')
    op.drop_column('Product', 'min_stock')
    op.drop_column('Product', 'cost')
    op.drop_column('Product', 'category_id')
    op.drop_column('Product', 'description')
    op.drop_column('Product', 'sku')
