"""Tests for the list-aircraft application use case."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from aeropulse.fleet.application.list_aircraft import ListAircraftHandler
from aeropulse.fleet.application.queries import ListAircraftQuery
from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.value_objects import AircraftRegistration


@dataclass
class RecordingAircraftReadRepository:
    aircraft: list[Aircraft]
    last_limit: int | None = None
    last_offset: int | None = None

    async def get_by_id(self, aircraft_id: UUID) -> Aircraft | None:
        return next((item for item in self.aircraft if item.id == aircraft_id), None)

    async def list_aircraft(self, *, limit: int, offset: int) -> list[Aircraft]:
        self.last_limit = limit
        self.last_offset = offset
        return self.aircraft[offset : offset + limit]

    async def count_aircraft(self) -> int:
        return len(self.aircraft)


def build_aircraft(index: int) -> Aircraft:
    return Aircraft(
        id=UUID(f"00000000-0000-4000-8000-{index:012d}"),
        registration=AircraftRegistration(f"T-{index:03d}"),
        created_at=datetime(2026, 11, 1, 10, index, tzinfo=UTC),
    )


def test_list_aircraft_returns_page_and_current_total() -> None:
    async def scenario() -> None:
        repository = RecordingAircraftReadRepository(
            aircraft=[build_aircraft(1), build_aircraft(2), build_aircraft(3)]
        )
        handler = ListAircraftHandler(repository)

        page = await handler.handle(ListAircraftQuery(limit=2, offset=1))

        assert [item.registration.value for item in page.items] == ["T-002", "T-003"]
        assert page.total == 3
        assert page.limit == 2
        assert page.offset == 1
        assert repository.last_limit == 2
        assert repository.last_offset == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("limit", "offset"),
    [
        (0, 0),
        (101, 0),
        (50, -1),
    ],
)
def test_list_aircraft_query_rejects_invalid_pagination(limit: int, offset: int) -> None:
    with pytest.raises(ValueError):
        ListAircraftQuery(limit=limit, offset=offset)
