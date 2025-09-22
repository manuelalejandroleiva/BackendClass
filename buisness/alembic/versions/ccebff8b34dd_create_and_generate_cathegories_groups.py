from alembic import op
import sqlalchemy as sa

revision = 'complete_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # ---- Roles ----

    # ---- Users ----
    # ---- Category ----
    op.create_table(
        'category',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False, unique=True)
    )

    # ---- Licencia ----
    
    # ---- Buisness ----
    

def downgrade():
    
    op.drop_table('category')
    
