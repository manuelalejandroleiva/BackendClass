"""add tipo_producto table and tipo_id to Product

Revision ID: 13_add_tipo_producto
Revises: 723224dee9d4
Create Date: 2026-07-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '13_add_tipo_producto'
down_revision: Union[str, Sequence[str], None] = '723224dee9d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tipo_producto (
            id SERIAL NOT NULL,
            nombre VARCHAR,
            PRIMARY KEY (id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tipo_producto_id ON tipo_producto (id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_tipo_producto_nombre ON tipo_producto (nombre)")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'Product' AND column_name = 'tipo_id'
            ) THEN
                ALTER TABLE "Product" ADD COLUMN tipo_id INTEGER REFERENCES tipo_producto(id);
            END IF;
        END
        $$;
    """)

    op.execute('CREATE INDEX IF NOT EXISTS ix_Product_tipo_id ON "Product" (tipo_id)')


def downgrade() -> None:
    op.drop_index(op.f('ix_Product_tipo_id'), table_name='Product')
    op.drop_column('Product', 'tipo_id')
    op.drop_table('tipo_producto')
