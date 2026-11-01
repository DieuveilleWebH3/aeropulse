"""Application-wide PostgreSQL and Redis runtime resources."""

import asyncio
import logging
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Protocol, cast

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from aeropulse.settings import Settings

logger = logging.getLogger(__name__)


class DatabaseConnection(Protocol):
    """Minimal database connection behavior required by the readiness probe."""

    async def execute(self, statement: object) -> object:
        """Execute a readiness statement."""
        ...


class DatabaseEngine(Protocol):
    """Minimal async database engine behavior owned by the runtime manager."""

    def connect(self) -> AbstractAsyncContextManager[DatabaseConnection]:
        """Open an async connection context."""
        ...

    async def dispose(self) -> None:
        """Dispose the engine and its pool."""
        ...


class RedisClient(Protocol):
    """Minimal Redis client behavior required by runtime management."""

    async def ping(self) -> bool:
        """Check Redis connectivity."""
        ...

    async def aclose(self) -> None:
        """Close the Redis client."""
        ...


@dataclass(slots=True)
class PostgresResource:
    """Manage PostgreSQL readiness and shutdown."""

    engine: DatabaseEngine

    async def is_ready(self) -> bool:
        """Return whether PostgreSQL accepts a simple query."""
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except (SQLAlchemyError, OSError, TimeoutError) as exc:
            logger.warning("PostgreSQL readiness check failed: %s", exc)
            return False
        return True

    async def close(self) -> None:
        """Dispose the PostgreSQL connection pool."""
        await self.engine.dispose()


@dataclass(slots=True)
class RedisResource:
    """Manage Redis readiness and shutdown."""

    client: RedisClient

    async def is_ready(self) -> bool:
        """Return whether Redis answers PING."""
        try:
            return bool(await self.client.ping())
        except (RedisError, OSError, TimeoutError) as exc:
            logger.warning("Redis readiness check failed: %s", exc)
            return False

    async def close(self) -> None:
        """Close the Redis client."""
        await self.client.aclose()


@dataclass(slots=True)
class ApplicationResources:
    """Own all critical application-wide runtime dependencies."""

    postgres: PostgresResource
    redis: RedisResource

    async def is_ready(self) -> bool:
        """Check critical dependencies concurrently."""
        postgres_ready, redis_ready = await asyncio.gather(
            self.postgres.is_ready(),
            self.redis.is_ready(),
        )
        return postgres_ready and redis_ready

    async def close(self) -> None:
        """Release all owned runtime dependencies."""
        await asyncio.gather(
            self.postgres.close(),
            self.redis.close(),
        )


def create_runtime_resources(settings: Settings) -> ApplicationResources:
    """Build runtime dependency clients without opening network connections eagerly."""
    timeout = settings.dependency_timeout_seconds

    engine: AsyncEngine = create_async_engine(
        settings.database_url.get_secret_value(),
        pool_pre_ping=True,
        connect_args={"timeout": timeout},
    )
    redis_client: Redis = Redis.from_url(
        settings.redis_url.get_secret_value(),
        decode_responses=True,
        socket_connect_timeout=timeout,
        socket_timeout=timeout,
    )

    return ApplicationResources(
        postgres=PostgresResource(engine=cast(DatabaseEngine, engine)),
        redis=RedisResource(client=cast(RedisClient, redis_client)),
    )
