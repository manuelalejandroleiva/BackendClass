"""remove business_type table and business_type_id column

Revision ID: 003_remove_business_type_table
Revises: 002_add_business_type_table, 06_add_reserved_vehiclestatus
Create Date: 2026-05-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


revision: str = '003_remove_business_type_table'
down_revision: Union[str, Sequence[str], None] = ('002_add_business_type_table', '06_add_reserved_vehiclestatus')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('fk_buisness_business_type', 'buisness', type_='foreignkey')
    op.drop_index(op.f('ix_buisness_business_type_id'), table_name='buisness')
    op.drop_column('buisness', 'business_type_id')

    op.drop_index(op.f('ix_business_types_name'), table_name='business_types')
    op.drop_index(op.f('ix_business_types_id'), table_name='business_types')
    op.drop_table('business_types')


def downgrade() -> None:
    op.create_table('business_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_business_types_id'), 'business_types', ['id'], unique=False)
    op.create_index(op.f('ix_business_types_name'), 'business_types', ['name'], unique=True)

    business_types_table = table('business_types',
        column('id', sa.Integer),
        column('name', sa.String)
    )
    op.bulk_insert(business_types_table, [
        {'id': 1, 'name': 'general'},
        {'id': 2, 'name': 'restaurant'},
        {'id': 3, 'name': 'store'},
    ])

    op.add_column('buisness',
        sa.Column('business_type_id', sa.Integer(), nullable=True)
    )
    op.create_index(op.f('ix_buisness_business_type_id'), 'buisness', ['business_type_id'], unique=False)
    op.create_foreign_key('fk_buisness_business_type', 'buisness', 'business_types', ['business_type_id'], ['id'])

    op.execute(
        "UPDATE buisness SET business_type_id = 1 WHERE business_type_id IS NULL"
    )

    op.alter_column('buisness', 'business_type_id', nullable=False)
