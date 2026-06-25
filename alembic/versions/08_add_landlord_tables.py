"""add landlord tables (properties, tenants, payments)

Revision ID: 08_add_landlord_tables
Revises: 5ac5b7557f7c
Create Date: 2026-06-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '08_add_landlord_tables'
down_revision: Union[str, Sequence[str], None] = '5ac5b7557f7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('properties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('landlord_id', sa.Integer(), nullable=False),
        sa.Column('monthly_rent', sa.Float(), server_default='0.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_properties_id', 'properties', ['id'])
    op.create_index('ix_properties_landlord_id', 'properties', ['landlord_id'])

    op.execute("CREATE TYPE payerstatus AS ENUM ('good_payer', 'bad_payer', 'regular')")
    op.execute("CREATE TYPE tenantstatus AS ENUM ('active', 'inactive')")
    op.execute("CREATE TYPE paymentmethod AS ENUM ('cash', 'transfer', 'deposit', 'rent', 'other')")

    op.create_table('tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('rent_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('deposit', sa.Float(), server_default='0.0'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'inactive', name='tenantstatus'), nullable=False, server_default='active'),
        sa.Column('payer_status', postgresql.ENUM('good_payer', 'bad_payer', 'regular', name='payerstatus'), nullable=False, server_default='regular'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tenants_id', 'tenants', ['id'])
    op.create_index('ix_tenants_property_id', 'tenants', ['property_id'])

    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('method', postgresql.ENUM('cash', 'transfer', 'deposit', 'rent', 'other', name='paymentmethod'), nullable=True, server_default='cash'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payments_id', 'payments', ['id'])
    op.create_index('ix_payments_tenant_id', 'payments', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('payments')
    op.drop_table('tenants')
    op.drop_table('properties')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS tenantstatus')
    op.execute('DROP TYPE IF EXISTS payerstatus')
