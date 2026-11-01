"""Tests for the get-aircraft application use case."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from aeropulse.fleet.application.errors import AircraftNotFound
from aeropulse.fleet.application.get_aircraft import GetAircraftHandler
from aeropulse.fleet.application.queries import GetAircraftQuery
from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.value_objects import AircraftRegistration

AIRCRAFT_ID = UUID("55555555-5555-4555-8555-555555555555")


@dataclass
class StubAircraftReadRepository:
    aircraft: Aircraft | None

    async def get_by_id(self, aircraft_id: UUID) -> Aircraft | None:
        if self.aircraft is not None and self.aircraft.id == aircraft_id:
            return self.aircraft
        return None

    async def list_aircraft(self, *, limit: int, offset: int) -> list[Aircraft]:
        del limit, offset
        return []

    async def count_aircraft(self) -> int:
        return 0


def test_get_aircraft_returns_existing_aggregate() -> None:
    async def scenario() -> None:
        aircraft = Aircraft(
            id=AIRCRAFT_ID,
            registration=AircraftRegistration("F-HABC"),
            created_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
        )
        handler = GetAircraftHandler(StubAircraftReadRepository(aircraft))

        result = await handler.handle(GetAircraftQuery(aircraft_id=AIRCRAFT_ID))

        assert result is aircraft

    asyncio.run(scenario())


def test_get_aircraft_raises_not_found_for_unknown_id() -> None:
    async def scenario() -> None:
        handler = GetAircraftHandler(StubAircraftReadRepository(None))

        with pytest.raises(AircraftNotFound, match=str(AIRCRAFT_ID)):
            await handler.handle(GetAircraftQuery(aircraft_id=AIRCRAFT_ID))

    asyncio.run(scenario())
