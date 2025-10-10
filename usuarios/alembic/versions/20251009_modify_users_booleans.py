from alembic import op
import sqlalchemy as sa

# Identificadores de la migración
revision = '20251009_modify_users_booleans'
down_revision = None # Cambia esto por la última migración aplicada
branch_labels = None
depends_on = None

def upgrade():
    # Cambiar is_active de Integer a Boolean
    op.alter_column(
        'users', 'is_active',
        existing_type=sa.Integer(),
        type_=sa.Boolean(),
        existing_nullable=False,
        postgresql_using='is_active::boolean'
    )

    # Cambiar is_verified de Integer a Boolean
    op.alter_column(
        'users', 'is_verified',
        existing_type=sa.Integer(),
        type_=sa.Boolean(),
        existing_nullable=False,
        postgresql_using='is_verified::boolean'
    )

def downgrade():
    # Revertir is_active a Integer
    op.alter_column(
        'users', 'is_active',
        existing_type=sa.Boolean(),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using='is_active::integer'
    )

    # Revertir is_verified a Integer
    op.alter_column(
        'users', 'is_verified',
        existing_type=sa.Boolean(),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using='is_verified::integer'
    )