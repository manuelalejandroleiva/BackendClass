from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "abcd1234efgh"
down_revision = None  # since this is the first migration
branch_labels = None
depends_on = None

def upgrade():
    # Create roles table first
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("name", sa.String, nullable=False, unique=True, index=True),
    )

    # Then create users table with FK referencing roles.id
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("email", sa.String, unique=True, index=True),
        sa.Column("address", sa.String),
        sa.Column("phone", sa.String),
        sa.Column("password", sa.String),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE")),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_verified", sa.Integer, nullable=False, server_default="0"),
    )

def downgrade():
    op.drop_table("users")
    op.drop_table("roles")
