"""Alembic migration environment for AeroPulse."""

import asyncio

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import create_async_engine

from aeropulse.fleet.infrastructure.persistence.schema import metadata
from aeropulse.settings import load_settings

target_metadata = metadata


def database_url() -> str:
    """Return the configured SQLAlchemy database URL."""
    return load_settings().database_url.get_secret_value()


def configure_context(connection: Connection) -> None:
    """Configure Alembic against one synchronous migration connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run online migrations through SQLAlchemy's async engine."""
    connectable = create_async_engine(
        database_url(),
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(configure_context)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Bridge Alembic's synchronous command API to asyncpg."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
