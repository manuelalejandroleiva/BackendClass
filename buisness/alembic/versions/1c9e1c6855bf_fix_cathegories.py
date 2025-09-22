"""Add foreign key from Buisness to Category

Revision ID: 1c9e1c6855bf
Revises: complete_initial_schema
Create Date: 2025-09-22 12:27:21.526504
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1c9e1c6855bf'
down_revision = 'complete_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema: link Buisness.categoria to Category.id"""
    # Crear la relación FK entre Buisness y Category
    op.create_foreign_key(
        "buisness_categoria_fkey",  # nombre explícito para la FK
        source_table="buisness",
        referent_table="category",
        local_cols=["categoria"],
        remote_cols=["id"],
    )


def downgrade() -> None:
    """Downgrade schema: eliminar FK entre Buisness y Category"""
    op.drop_constraint(
        "buisness_categoria_fkey",
        table_name="buisness",
        type_="foreignkey"
    )
