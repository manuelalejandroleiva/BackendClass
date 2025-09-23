"""create initial tables

Revision ID: 123456789abc
Revises: 
Create Date: 2025-09-23

"""
from alembic import op
import sqlalchemy as sa

# Identificadores de Alembic
revision = '123456789abc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Licencia
    op.create_table(
        'licencia',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False, unique=True, index=True),
    )

    # Category
    op.create_table(
        'category',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False, unique=True, index=True),
    )

    # Buisness
    op.create_table(
        'buisness',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('capital_money', sa.Integer(), index=True),
        sa.Column('licencia_id', sa.Integer(), sa.ForeignKey('licencia.id')),
        sa.Column('permisos', sa.String(), index=True),
        sa.Column('categoria', sa.Integer(), sa.ForeignKey('category.id')),
        sa.Column('email', sa.String(), unique=True, index=True),
        sa.Column('phone', sa.String(), index=True),
        sa.Column('address', sa.String(), index=True),
    )

    # Tables
    op.create_table(
        'Tables',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), unique=True, index=True),
        sa.Column('capacity', sa.Integer(), index=True),
        sa.Column('buisness_id', sa.Integer(), sa.ForeignKey('buisness.id')),
        sa.Column('status', sa.String(), index=True, nullable=True),   # libre, ocupada, reservada
        sa.Column('location', sa.String(), index=True, nullable=True), # interior, exterior, barra
    )

    # Product
    op.create_table(
        'Product',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), unique=True, index=True),
        sa.Column('price', sa.Integer(), index=True),
        sa.Column('stock', sa.Integer(), index=True),
        sa.Column('buisness_id', sa.Integer(), sa.ForeignKey('buisness.id')),
    )


def downgrade():
    op.drop_table('Product')
    op.drop_table('Tables')
    op.drop_table('buisness')
    op.drop_table('category')
    op.drop_table('licencia')
