"""Unit tests for application-wide runtime resource management."""

import asyncio
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from types import TracebackType

from aeropulse.platform.resources import (
    ApplicationResources,
    DatabaseConnection,
    PostgresResource,
    RedisResource,
    create_runtime_resources,
)
from aeropulse.settings import Settings


class FakeConnection:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.executed = False

    async def execute(self, statement: object) -> object:
        del statement
        if self.error is not None:
            raise self.error
        self.executed = True
        return object()


class FakeConnectionContext(AbstractAsyncContextManager[DatabaseConnection]):
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> DatabaseConnection:
        return self.connection

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback


@dataclass
class FakeDatabaseEngine:
    connection: FakeConnection
    disposed: bool = False

    def connect(self) -> AbstractAsyncContextManager[DatabaseConnection]:
        return FakeConnectionContext(self.connection)

    async def dispose(self) -> None:
        self.disposed = True


@dataclass
class FakeRedisClient:
    ready: bool = True
    error: Exception | None = None
    closed: bool = False

    async def ping(self) -> bool:
        if self.error is not None:
            raise self.error
        return self.ready

    async def aclose(self) -> None:
        self.closed = True


def test_postgres_resource_reports_ready_and_disposes_engine() -> None:
    async def scenario() -> None:
        connection = FakeConnection()
        engine = FakeDatabaseEngine(connection)
        resource = PostgresResource(engine=engine)

        assert await resource.is_ready() is True
        assert connection.executed is True

        await resource.close()

        assert engine.disposed is True

    asyncio.run(scenario())


def test_postgres_resource_reports_unavailable_on_connection_error() -> None:
    async def scenario() -> None:
        engine = FakeDatabaseEngine(FakeConnection(error=OSError("database unavailable")))
        resource = PostgresResource(engine=engine)

        assert await resource.is_ready() is False

    asyncio.run(scenario())


def test_redis_resource_reports_ready_and_closes_client() -> None:
    async def scenario() -> None:
        client = FakeRedisClient()
        resource = RedisResource(client=client)

        assert await resource.is_ready() is True

        await resource.close()

        assert client.closed is True

    asyncio.run(scenario())


def test_redis_resource_reports_unavailable_on_connection_error() -> None:
    async def scenario() -> None:
        client = FakeRedisClient(error=OSError("redis unavailable"))
        resource = RedisResource(client=client)

        assert await resource.is_ready() is False

    asyncio.run(scenario())


def test_application_resources_require_all_dependencies_to_be_ready() -> None:
    async def scenario() -> None:
        postgres_engine = FakeDatabaseEngine(FakeConnection())
        redis_client = FakeRedisClient(ready=True)
        resources = ApplicationResources(
            postgres=PostgresResource(postgres_engine),
            redis=RedisResource(redis_client),
        )

        assert await resources.is_ready() is True

        redis_client.ready = False

        assert await resources.is_ready() is False

        await resources.close()

        assert postgres_engine.disposed is True
        assert redis_client.closed is True

    asyncio.run(scenario())


def test_runtime_resource_factory_builds_and_closes_clients_without_connecting() -> None:
    async def scenario() -> None:
        settings = Settings.model_validate(
            {
                "database_url": ("postgresql+asyncpg://user:password@127.0.0.1:5432/aeropulse"),
                "redis_url": "redis://127.0.0.1:6379/0",
                "dependency_timeout_seconds": 0.1,
            }
        )
        resources = create_runtime_resources(settings)

        assert isinstance(resources.postgres, PostgresResource)
        assert isinstance(resources.redis, RedisResource)

        await resources.close()

    asyncio.run(scenario())
