"""Actualizar tabla buisness

Revision ID: 5d636450d6e8
Revises: 
Create Date: 2025-10-28 13:43:17.886989
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5d636450d6e8'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Upgrade schema."""
    # Agregar columnas nuevas
    op.add_column('buisness', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('buisness', sa.Column('image_path', sa.String(), nullable=True))
    
    # Cambiar columna 'name' para permitir nulos
    op.alter_column('buisness', 'name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    
    # Crear índice para user_id
    op.create_index(op.f('ix_buisness_user_id'), 'buisness', ['user_id'], unique=False)
    
    # Eliminar columnas antiguas
    op.drop_constraint(op.f('buisness_licencia_id_fkey'), 'buisness', type_='foreignkey')
    op.drop_column('buisness', 'licencia_id')
    op.drop_column('buisness', 'permisos')


def downgrade() -> None:
    """Downgrade schema."""
    # Restaurar columnas eliminadas
    op.add_column('buisness', sa.Column('licencia_id', sa.INTEGER(), nullable=True))
    op.add_column('buisness', sa.Column('permisos', sa.VARCHAR(), nullable=True))
    op.create_foreign_key(op.f('buisness_licencia_id_fkey'), 'buisness', 'licencia', ['licencia_id'], ['id'])
    
    # Eliminar columnas nuevas
    op.drop_index(op.f('ix_buisness_user_id'), table_name='buisness')
    op.drop_column('buisness', 'user_id')
    op.drop_column('buisness', 'image_path')
    
    # Restaurar columna 'name' a no nullable
    op.alter_column('buisness', 'name',
               existing_type=sa.VARCHAR(),
               nullable=False)
