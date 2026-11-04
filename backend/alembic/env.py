"""Alembic migration environment."""
import os
import sys
from logging.config import fileConfig

from alembic import context

sys.path.insert(0, os.path.abspath("."))

from app.core.database import Base, engine
import app.models  # noqa: F401  (registers every table on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

if "DATABASE_URL" in os.environ:
    config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])


def run_migrations_offline() -> None:
    url = str(engine.url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())
