"""PostgreSQL integration tests for Fleet aircraft read persistence."""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from aeropulse.fleet.domain.aircraft import AircraftStatus
from aeropulse.fleet.infrastructure.persistence.repository import SqlAlchemyAircraftRepository
from aeropulse.fleet.infrastructure.persistence.schema import aircraft_table
from aeropulse.settings import load_settings

pytestmark = [
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to test PostgreSQL persistence",
    ),
]

IDS = [
    UUID("66666666-6666-4666-8666-666666666661"),
    UUID("66666666-6666-4666-8666-666666666662"),
    UUID("66666666-6666-4666-8666-666666666663"),
]


async def seed_aircraft() -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    base_time = datetime(2000, 1, 1, 0, 0, tzinfo=UTC)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                insert(aircraft_table),
                [
                    {
                        "id": IDS[0],
                        "registration": "R-001",
                        "status": "active",
                        "created_at": base_time,
                        "retired_at": None,
                    },
                    {
                        "id": IDS[1],
                        "registration": "R-002",
                        "status": "retired",
                        "created_at": base_time + timedelta(minutes=1),
                        "retired_at": base_time + timedelta(days=1),
                    },
                    {
                        "id": IDS[2],
                        "registration": "R-003",
                        "status": "active",
                        "created_at": base_time + timedelta(minutes=2),
                        "retired_at": None,
                    },
                ],
            )
    finally:
        await engine.dispose()


async def cleanup_aircraft() -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            await connection.execute(delete(aircraft_table).where(aircraft_table.c.id.in_(IDS)))
    finally:
        await engine.dispose()


def test_repository_get_by_id_rehydrates_persisted_status() -> None:
    async def scenario() -> None:
        await cleanup_aircraft()
        await seed_aircraft()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as session:
                aircraft = await SqlAlchemyAircraftRepository(session).get_by_id(IDS[1])

            assert aircraft is not None
            assert aircraft.id == IDS[1]
            assert aircraft.registration.value == "R-002"
            assert aircraft.status is AircraftStatus.RETIRED
            assert aircraft.retired_at == datetime(2000, 1, 2, 0, 0, tzinfo=UTC)
        finally:
            await engine.dispose()
            await cleanup_aircraft()

    asyncio.run(scenario())


def test_repository_lists_deterministically_with_limit_offset_and_total() -> None:
    async def scenario() -> None:
        await cleanup_aircraft()
        await seed_aircraft()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as session:
                repository = SqlAlchemyAircraftRepository(session)
                items = await repository.list_aircraft(limit=2, offset=1)
                total = await repository.count_aircraft()

            registrations = [item.registration.value for item in items]
            assert registrations == ["R-002", "R-003"]
            assert total >= 3
        finally:
            await engine.dispose()
            await cleanup_aircraft()

    asyncio.run(scenario())
