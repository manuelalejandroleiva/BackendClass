"""add_restaurant_tables_stripe

Revision ID: c36be2a186b6
Revises: 04f84973a28f
Create Date: 2026-05-25 15:57:30.452449

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c36be2a186b6'
down_revision: Union[str, Sequence[str], None] = '04f84973a28f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('menu_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('price', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(), nullable=True),
    sa.Column('available', sa.Boolean(), nullable=True),
    sa.Column('business_id', sa.Integer(), nullable=True),
    sa.Column('image', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['buisness.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_menu_items_business_id'), 'menu_items', ['business_id'], unique=False)
    op.create_index(op.f('ix_menu_items_category'), 'menu_items', ['category'], unique=False)
    op.create_index(op.f('ix_menu_items_id'), 'menu_items', ['id'], unique=False)
    op.create_index(op.f('ix_menu_items_name'), 'menu_items', ['name'], unique=False)
    op.create_index(op.f('ix_menu_items_price'), 'menu_items', ['price'], unique=False)

    op.create_table('monthly_closings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('business_id', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('total_sales', sa.Integer(), nullable=True),
    sa.Column('total_cash', sa.Integer(), nullable=True),
    sa.Column('total_card', sa.Integer(), nullable=True),
    sa.Column('total_transactions', sa.Integer(), nullable=True),
    sa.Column('total_discounts', sa.Integer(), nullable=True),
    sa.Column('closed_at', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['buisness.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monthly_closings_business_id'), 'monthly_closings', ['business_id'], unique=False)
    op.create_index(op.f('ix_monthly_closings_id'), 'monthly_closings', ['id'], unique=False)
    op.create_index(op.f('ix_monthly_closings_month'), 'monthly_closings', ['month'], unique=False)
    op.create_index(op.f('ix_monthly_closings_status'), 'monthly_closings', ['status'], unique=False)
    op.create_index(op.f('ix_monthly_closings_year'), 'monthly_closings', ['year'], unique=False)

    op.create_table('restaurant_orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('table_id', sa.Integer(), nullable=True),
    sa.Column('business_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('total', sa.Integer(), nullable=True),
    sa.Column('notes', sa.String(), nullable=True),
    sa.Column('created_at', sa.String(), nullable=True),
    sa.Column('updated_at', sa.String(), nullable=True),
    sa.Column('stripe_payment_intent_id', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['business_id'], ['buisness.id'], ),
    sa.ForeignKeyConstraint(['table_id'], ['Tables.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_restaurant_orders_business_id'), 'restaurant_orders', ['business_id'], unique=False)
    op.create_index(op.f('ix_restaurant_orders_created_at'), 'restaurant_orders', ['created_at'], unique=False)
    op.create_index(op.f('ix_restaurant_orders_id'), 'restaurant_orders', ['id'], unique=False)
    op.create_index(op.f('ix_restaurant_orders_status'), 'restaurant_orders', ['status'], unique=False)
    op.create_index(op.f('ix_restaurant_orders_stripe_payment_intent_id'), 'restaurant_orders', ['stripe_payment_intent_id'], unique=False)
    op.create_index(op.f('ix_restaurant_orders_table_id'), 'restaurant_orders', ['table_id'], unique=False)

    op.create_table('restaurant_order_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=True),
    sa.Column('menu_item_id', sa.Integer(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=True),
    sa.Column('unit_price', sa.Integer(), nullable=True),
    sa.Column('subtotal', sa.Integer(), nullable=True),
    sa.Column('notes', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['menu_item_id'], ['menu_items.id'], ),
    sa.ForeignKeyConstraint(['order_id'], ['restaurant_orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_restaurant_order_items_id'), 'restaurant_order_items', ['id'], unique=False)
    op.create_index(op.f('ix_restaurant_order_items_menu_item_id'), 'restaurant_order_items', ['menu_item_id'], unique=False)
    op.create_index(op.f('ix_restaurant_order_items_order_id'), 'restaurant_order_items', ['order_id'], unique=False)


def downgrade() -> None:
    op.drop_table('restaurant_order_items')
    op.drop_table('restaurant_orders')
    op.drop_table('monthly_closings')
    op.drop_table('menu_items')
