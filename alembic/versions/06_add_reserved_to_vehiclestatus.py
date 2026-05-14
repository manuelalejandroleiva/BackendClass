"""add reserved to vehiclestatus enum

Revision ID: 06_add_reserved_vehiclestatus
Revises: 05_add_rentas
Create Date: 2026-05-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '06_add_reserved_vehiclestatus'
down_revision: Union[str, Sequence[str], None] = '05_add_rentas'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar 'RESERVED' al enum vehiclestatus
    op.execute("ALTER TYPE vehiclestatus ADD VALUE IF NOT EXISTS 'RESERVED'")


def downgrade() -> None:
    # PostgreSQL no soporta remover valores de un enum fácilmente
    # Necesitamos recrear el enum sin RESERVED
    op.execute("""
        ALTER TYPE vehiclestatus RENAME TO vehiclestatus_old;
        
        CREATE TYPE vehiclestatus AS ENUM ('AVAILABLE', 'RENTED', 'MAINTENANCE', 'INACTIVE');
        
        ALTER TABLE vehicles 
            ALTER COLUMN status TYPE vehiclestatus 
            USING status::text::vehiclestatus;
        
        DROP TYPE vehiclestatus_old;
    """)
