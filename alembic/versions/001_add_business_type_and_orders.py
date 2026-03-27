"""add business_type and orders tables

Revision ID: 001_add_business_type_and_orders
Revises: 3e452cdc72cb
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_business_type_and_orders'
down_revision = '3e452cdc72cb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add business_type to buisness table
    op.add_column('buisness', sa.Column('business_type', sa.String(), nullable=True, index=True))
    op.execute("UPDATE buisness SET business_type = 'general' WHERE business_type IS NULL")
    op.alter_column('buisness', 'business_type', nullable=False, existing_nullable=True)

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('table_id', sa.Integer(), nullable=True, index=True),
        sa.Column('business_id', sa.Integer(), nullable=True, index=True),
        sa.Column('status', sa.String(), nullable=True, index=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('total', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True, index=True),
        sa.Column('updated_at', sa.String(), nullable=True),
    )

    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), nullable=True, index=True),
        sa.Column('product_id', sa.Integer(), nullable=True, index=True),
        sa.Column('product_name', sa.String(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('unit_price', sa.Integer(), nullable=True),
        sa.Column('subtotal', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_column('buisness', 'business_type')
