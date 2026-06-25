from dotenv import load_dotenv
import os
load_dotenv()  

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import Base and models for autogenerate
from common.database import Base
from common.models import (
    Role, User, Category, Buisness, Tables, Product, Sale,
    Order, OrderItem, MenuItem, MonthlyClosing, TipoMesa,
    LegacyOrder, LegacyOrderItem
)
from rentas.models.models import Vehicle, GPSLocation, Rental, Geofence, GeofenceAlert
from landlord.models.models import Property, Tenant, Payment

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    db_url = os.getenv("DATABASE_URL_ALEMBIC")
    url = db_url if db_url else config.get_main_option("sqlalchemy.url")
    
    if not url:
        raise ValueError("DATABASE_URL_ALEMBIC environment variable or sqlalchemy.url in config must be set")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    raw_db_url = os.getenv("DATABASE_URL_ALEMBIC")
    if not raw_db_url:
        raise ValueError("DATABASE_URL_ALEMBIC environment variable must be set")

    # Expand ${...} placeholders if present
    db_url = os.path.expandvars(raw_db_url)

    # Convert asyncpg to psycopg2 for alembic sync
    sync_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = sync_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
