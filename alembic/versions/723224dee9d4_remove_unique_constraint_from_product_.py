"""remove unique constraint from product name

Revision ID: 723224dee9d4
Revises: 12_add_product_category_fk
Create Date: 2026-07-02 20:36:49.721811

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '723224dee9d4'
down_revision: Union[str, Sequence[str], None] = '12_add_product_category_fk'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_Product_name'), table_name='Product')
    op.create_index(op.f('ix_Product_name'), 'Product', ['name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_Product_name'), table_name='Product')
    op.create_index(op.f('ix_Product_name'), 'Product', ['name'], unique=True)
