"""add tipo_mesa table, drop business_resources and wash_cycles

Revision ID: 07_add_tipo_mesa
Revises: 06_add_reserved_vehiclestatus
Create Date: 2026-06-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '07_add_tipo_mesa'
down_revision: Union[str, Sequence[str], None] = '003_remove_business_type_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tipo_mesa (
            id SERIAL NOT NULL,
            nombre VARCHAR,
            PRIMARY KEY (id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tipo_mesa_id ON tipo_mesa (id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_tipo_mesa_nombre ON tipo_mesa (nombre)")

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'Tables' AND column_name = 'tipo_id'
            ) THEN
                ALTER TABLE "Tables" ADD COLUMN tipo_id INTEGER REFERENCES tipo_mesa(id);
            END IF;
        END
        $$;
    """)

    op.execute("""
        INSERT INTO tipo_mesa (id, nombre) VALUES (1, 'mesa')
        ON CONFLICT (id) DO NOTHING
    """)
    op.execute("""
        INSERT INTO tipo_mesa (id, nombre) VALUES (2, 'lavadora')
        ON CONFLICT (id) DO NOTHING
    """)

    op.execute("DROP TABLE IF EXISTS wash_cycles CASCADE")
    op.execute("DROP TABLE IF EXISTS business_resources CASCADE")


def downgrade() -> None:
    op.create_table('business_resources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), server_default='available'),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('capacity_kg', sa.Integer(), nullable=True),
        sa.Column('price_per_load', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_resources_id', 'business_resources', ['id'])
    op.create_index('ix_business_resources_name', 'business_resources', ['name'])
    op.create_index('ix_business_resources_business_id', 'business_resources', ['business_id'])
    op.create_index('ix_business_resources_status', 'business_resources', ['status'])
    op.create_index('ix_business_resources_resource_type', 'business_resources', ['resource_type'])

    op.create_table('wash_cycles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('business_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.String(), nullable=True),
        sa.Column('ended_at', sa.String(), nullable=True),
        sa.Column('price_per_load', sa.Integer(), nullable=True),
        sa.Column('total_price', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), server_default='in_progress'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wash_cycles_id', 'wash_cycles', ['id'])
    op.create_index('ix_wash_cycles_resource_id', 'wash_cycles', ['resource_id'])
    op.create_index('ix_wash_cycles_business_id', 'wash_cycles', ['business_id'])
    op.create_index('ix_wash_cycles_status', 'wash_cycles', ['status'])

    op.drop_column('Tables', 'tipo_id')
    op.drop_table('tipo_mesa')
