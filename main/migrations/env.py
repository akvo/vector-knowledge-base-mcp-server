import os
import sys
import logging

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool, create_engine, text
from alembic import context
from psycopg2 import DatabaseError

from app.db.connection import Base
from app.core.config import settings


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

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
logger = logging.getLogger("alembic.env")

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    """
    if settings.testing:
        raise DatabaseError("Test migrations offline is not permitted.")

    context.configure(
        url=settings.database_url,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    """
    DB_URL = (
        f"{settings.database_url}_test"
        if settings.testing
        else settings.database_url
    )
    # handle testing config for migrations
    if settings.testing:
        # connect to primary db
        default_engine = create_engine(
            settings.database_url, isolation_level="AUTOCOMMIT"
        )
        # drop testing db if it exists and create a fresh one
        with default_engine.connect() as default_conn:
            default_conn.execute(text("DROP DATABASE IF EXISTS kb_mcp_test"))
            default_conn.execute(text("CREATE DATABASE kb_mcp_test"))
    connectable = config.attributes.get("connection", None)
    config.set_main_option("sqlalchemy.url", DB_URL)

    if connectable is None:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    logger.info("Running migrations offline")
    run_migrations_offline()
else:
    logger.info("Running migrations online")
    run_migrations_online()
