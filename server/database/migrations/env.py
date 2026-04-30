from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import os
import sys

# 1. Add project root to path to import connection.py
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

# 2. Import the dynamic engine and metadata
from database.connection import engine as app_engine
from database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use the URL from our connection logic
    from database.connection import get_connection_url
    url = str(get_connection_url()) # Helper returns URL object or string
    
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
    # 3. Use the engine already configured in connection.py
    connectable = app_engine

    with connectable.connect() as connection:
        # 4. Detect Dialect
        is_sqlite = connection.dialect.name == "sqlite"
        
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # 5. Enable Batch Mode conditionally for SQLite
            render_as_batch=is_sqlite 
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
