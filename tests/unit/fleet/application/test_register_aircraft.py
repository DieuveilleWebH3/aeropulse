"""Tests for the register-aircraft application use case."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import pytest

from aeropulse.fleet.application.commands import RegisterAircraftCommand
from aeropulse.fleet.application.errors import AircraftRegistrationAlreadyExists
from aeropulse.fleet.application.register_aircraft import RegisterAircraftHandler
from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.errors import InvalidAircraftRegistration
from aeropulse.fleet.domain.value_objects import AircraftRegistration

AIRCRAFT_ID = UUID("22222222-2222-4222-8222-222222222222")
NOW = datetime(2026, 11, 1, 9, 0, tzinfo=UTC)


@dataclass
class InMemoryAircraftRepository:
    registrations: set[AircraftRegistration] = field(default_factory=set)
    added: list[Aircraft] = field(default_factory=list)

    async def exists_by_registration(self, registration: AircraftRegistration) -> bool:
        return registration in self.registrations

    async def add(self, aircraft: Aircraft) -> None:
        self.added.append(aircraft)
        self.registrations.add(aircraft.registration)


def test_register_aircraft_creates_active_aircraft_with_injected_id_and_clock() -> None:
    async def scenario() -> None:
        repository = InMemoryAircraftRepository()
        handler = RegisterAircraftHandler(
            repository,
            id_generator=lambda: AIRCRAFT_ID,
            clock=lambda: NOW,
        )

        aircraft = await handler.handle(RegisterAircraftCommand(registration=" f-habc "))

        assert aircraft.id == AIRCRAFT_ID
        assert aircraft.registration == AircraftRegistration("F-HABC")
        assert aircraft.status is AircraftStatus.ACTIVE
        assert aircraft.created_at == NOW
        assert repository.added == [aircraft]

    asyncio.run(scenario())


def test_register_aircraft_rejects_case_insensitive_duplicate() -> None:
    async def scenario() -> None:
        repository = InMemoryAircraftRepository(registrations={AircraftRegistration("F-HABC")})
        handler = RegisterAircraftHandler(
            repository,
            id_generator=lambda: AIRCRAFT_ID,
            clock=lambda: NOW,
        )

        with pytest.raises(
            AircraftRegistrationAlreadyExists,
            match="F-HABC",
        ):
            await handler.handle(RegisterAircraftCommand(registration=" f-habc "))

        assert repository.added == []

    asyncio.run(scenario())


def test_invalid_registration_is_rejected_before_repository_lookup() -> None:
    class RepositoryThatMustNotBeCalled:
        async def exists_by_registration(self, registration: AircraftRegistration) -> bool:
            del registration
            raise AssertionError("repository lookup must not run for invalid registration")

        async def add(self, aircraft: Aircraft) -> None:
            del aircraft
            raise AssertionError("repository add must not run for invalid registration")

    async def scenario() -> None:
        handler = RegisterAircraftHandler(RepositoryThatMustNotBeCalled())

        with pytest.raises(InvalidAircraftRegistration):
            await handler.handle(RegisterAircraftCommand(registration="   "))

    asyncio.run(scenario())
