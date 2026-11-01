"""PostgreSQL integration tests for Fleet aircraft persistence."""

import asyncio
import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.repositories import AircraftRegistrationConflict
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


def unique_registration() -> AircraftRegistration:
    """Return a canonical test registration that is unique across local reruns."""
    return AircraftRegistration(f"T-{uuid4().hex[:8]}")


def aircraft_for(registration: AircraftRegistration, *, id: UUID | None = None) -> Aircraft:
    """Build a deterministic-shape Aircraft for persistence tests."""
    return Aircraft(
        id=id or uuid4(),
        registration=registration,
        created_at=datetime.now(UTC),
    )


def test_repository_does_not_commit_caller_transaction() -> None:
    async def scenario() -> None:
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        registration = unique_registration()
        aircraft = aircraft_for(registration)

        try:
            async with session_factory() as writer, writer.begin():
                repository = SqlAlchemyAircraftRepository(writer)
                await repository.add(aircraft)

                async with session_factory() as observer:
                    observer_repository = SqlAlchemyAircraftRepository(observer)
                    assert await observer_repository.exists_by_registration(registration) is False

            async with session_factory() as observer:
                observer_repository = SqlAlchemyAircraftRepository(observer)
                assert await observer_repository.exists_by_registration(registration) is True
        finally:
            async with session_factory.begin() as cleanup_session:
                await cleanup_session.execute(
                    delete(aircraft_table).where(aircraft_table.c.id == aircraft.id)
                )
            await engine.dispose()

    asyncio.run(scenario())


def test_repository_translates_named_registration_unique_constraint() -> None:
    async def scenario() -> None:
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        registration = unique_registration()
        first = aircraft_for(registration)
        second = aircraft_for(registration)

        try:
            async with session_factory.begin() as session:
                await SqlAlchemyAircraftRepository(session).add(first)

            with pytest.raises(AircraftRegistrationConflict, match=str(registration)):
                async with session_factory.begin() as session:
                    await SqlAlchemyAircraftRepository(session).add(second)
        finally:
            async with session_factory.begin() as cleanup_session:
                await cleanup_session.execute(
                    delete(aircraft_table).where(
                        aircraft_table.c.registration == registration.value
                    )
                )
            await engine.dispose()

    asyncio.run(scenario())
