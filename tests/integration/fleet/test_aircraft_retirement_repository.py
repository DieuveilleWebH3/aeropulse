"""PostgreSQL integration tests for conditional aircraft retirement."""

import asyncio
import os
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.repositories import AircraftRetirementConflict
from aeropulse.fleet.domain.value_objects import AircraftRegistration
from aeropulse.fleet.infrastructure.persistence.repository import (
    SqlAlchemyAircraftRepository,
)
from aeropulse.fleet.infrastructure.persistence.schema import aircraft_table
from aeropulse.settings import load_settings

pytestmark = [
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to test PostgreSQL persistence",
    ),
]

AIRCRAFT_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
CREATED_AT = datetime(2001, 1, 1, 10, 0, tzinfo=UTC)
RETIRED_AT = datetime(2001, 1, 2, 10, 0, tzinfo=UTC)


async def cleanup() -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            await connection.execute(
                delete(aircraft_table).where(aircraft_table.c.id == AIRCRAFT_ID)
            )
    finally:
        await engine.dispose()


async def seed_active() -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            await connection.execute(
                insert(aircraft_table).values(
                    id=AIRCRAFT_ID,
                    registration="LIFE-001",
                    status="active",
                    created_at=CREATED_AT,
                    retired_at=None,
                )
            )
    finally:
        await engine.dispose()


def test_repository_persists_retirement_and_rehydrates_timestamp() -> None:
    async def scenario() -> None:
        await cleanup()
        await seed_active()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory.begin() as session:
                repository = SqlAlchemyAircraftRepository(session)
                aircraft = await repository.get_by_id(AIRCRAFT_ID)
                assert aircraft is not None
                assert aircraft.retire(retired_at=RETIRED_AT) is True
                await repository.update_retirement(aircraft)

            async with session_factory() as session:
                persisted = await SqlAlchemyAircraftRepository(session).get_by_id(AIRCRAFT_ID)

            assert persisted is not None
            assert persisted.status is AircraftStatus.RETIRED
            assert persisted.retired_at == RETIRED_AT
        finally:
            await engine.dispose()
            await cleanup()

    asyncio.run(scenario())


def test_repository_rejects_second_retirement_without_overwriting_timestamp() -> None:
    async def scenario() -> None:
        await cleanup()
        await seed_active()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        first = Aircraft.rehydrate(
            id=AIRCRAFT_ID,
            registration=AircraftRegistration("LIFE-001"),
            status=AircraftStatus.ACTIVE,
            created_at=CREATED_AT,
            retired_at=None,
        )
        first.retire(retired_at=RETIRED_AT)

        stale = Aircraft.rehydrate(
            id=AIRCRAFT_ID,
            registration=AircraftRegistration("LIFE-001"),
            status=AircraftStatus.ACTIVE,
            created_at=CREATED_AT,
            retired_at=None,
        )
        stale.retire(retired_at=datetime(2001, 1, 3, 10, 0, tzinfo=UTC))

        try:
            async with session_factory.begin() as session:
                await SqlAlchemyAircraftRepository(session).update_retirement(first)

            with pytest.raises(AircraftRetirementConflict):
                async with session_factory.begin() as session:
                    await SqlAlchemyAircraftRepository(session).update_retirement(stale)

            async with engine.connect() as connection:
                result = await connection.execute(
                    select(aircraft_table.c.retired_at).where(aircraft_table.c.id == AIRCRAFT_ID)
                )
                retired_at = result.scalar_one()

            assert retired_at == RETIRED_AT
        finally:
            await engine.dispose()
            await cleanup()

    asyncio.run(scenario())


def test_database_rejects_active_aircraft_with_retirement_timestamp() -> None:
    async def scenario() -> None:
        await cleanup()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())

        try:
            with pytest.raises(IntegrityError):
                async with engine.begin() as connection:
                    await connection.execute(
                        insert(aircraft_table).values(
                            id=AIRCRAFT_ID,
                            registration="LIFE-002",
                            status="active",
                            created_at=CREATED_AT,
                            retired_at=RETIRED_AT,
                        )
                    )
        finally:
            await engine.dispose()
            await cleanup()

    asyncio.run(scenario())


def test_database_rejects_retirement_before_registration() -> None:
    async def scenario() -> None:
        await cleanup()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())

        try:
            with pytest.raises(IntegrityError):
                async with engine.begin() as connection:
                    await connection.execute(
                        insert(aircraft_table).values(
                            id=AIRCRAFT_ID,
                            registration="LIFE-003",
                            status="retired",
                            created_at=CREATED_AT,
                            retired_at=datetime(2000, 12, 31, 10, 0, tzinfo=UTC),
                        )
                    )
        finally:
            await engine.dispose()
            await cleanup()

    asyncio.run(scenario())
