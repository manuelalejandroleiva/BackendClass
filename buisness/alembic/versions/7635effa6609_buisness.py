"""create Licencia and Buisness tables

Revision ID: 7635effa6609
Revises: 
Create Date: 2025-08-06 15:15:43.002179
"""

from alembic import op
import sqlalchemy as sa
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '7635effa6609'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Upgrade schema."""

    # Crear tabla Licencia
    op.create_table(
        'Licencia',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
    )
    op.create_index('ix_Licencia_id', 'Licencia', ['id'])
    op.create_index('ix_Licencia_name', 'Licencia', ['name'], unique=True)

    # Crear tabla Buisness
    op.create_table(
        'Buisness',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('capital_money', sa.Integer(), nullable=True),
        sa.Column('licencia_id', sa.Integer(), sa.ForeignKey('Licencia.id'), nullable=True),
        sa.Column('permisos', sa.String(), nullable=True),
        sa.Column('categoria', sa.Integer(), nullable=True),
    )
    op.create_index('ix_Buisness_id', 'Buisness', ['id'])
    op.create_index('ix_Buisness_name', 'Buisness', ['name'], unique=True)
    op.create_index('ix_Buisness_capital_money', 'Buisness', ['capital_money'])
    op.create_index('ix_Buisness_categoria', 'Buisness', ['categoria'])
    op.create_index('ix_Buisness_permisos', 'Buisness', ['permisos'])


def downgrade():
    """Downgrade schema."""

    # Eliminar tabla Buisness
    op.drop_index('ix_Buisness_permisos', table_name='Buisness')
    op.drop_index('ix_Buisness_categoria', table_name='Buisness')
    op.drop_index('ix_Buisness_capital_money', table_name='Buisness')
    op.drop_index('ix_Buisness_name', table_name='Buisness')
    op.drop_index('ix_Buisness_id', table_name='Buisness')
    op.drop_table('Buisness')

    # Eliminar tabla Licencia
    op.drop_index('ix_Licencia_name', table_name='Licencia')
    op.drop_index('ix_Licencia_id', table_name='Licencia')
    op.drop_table('Licencia')
