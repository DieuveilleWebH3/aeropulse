"""Tests for the retire-aircraft application use case."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from aeropulse.fleet.application.commands import RetireAircraftCommand
from aeropulse.fleet.application.errors import AircraftNotFound
from aeropulse.fleet.application.retire_aircraft import RetireAircraftHandler
from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.repositories import AircraftRetirementConflict
from aeropulse.fleet.domain.value_objects import AircraftRegistration

AIRCRAFT_ID = UUID("99999999-9999-4999-8999-999999999999")
CREATED_AT = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)
RETIRED_AT = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def active_aircraft() -> Aircraft:
    return Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=CREATED_AT,
    )


def retired_aircraft(*, retired_at: datetime = RETIRED_AT) -> Aircraft:
    return Aircraft.rehydrate(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        status=AircraftStatus.RETIRED,
        created_at=CREATED_AT,
        retired_at=retired_at,
    )


@dataclass
class RecordingLifecycleRepository:
    aircraft: Aircraft | None
    update_calls: int = 0
    conflict_on_update: bool = False
    concurrent_result: Aircraft | None = None

    async def get_by_id(self, aircraft_id: UUID) -> Aircraft | None:
        if self.conflict_on_update and self.update_calls > 0:
            return self.concurrent_result
        if self.aircraft is not None and self.aircraft.id == aircraft_id:
            return self.aircraft
        return None

    async def update_retirement(self, aircraft: Aircraft) -> None:
        self.update_calls += 1
        if self.conflict_on_update:
            raise AircraftRetirementConflict(aircraft.id)
        self.aircraft = aircraft


def test_retire_aircraft_updates_active_aircraft_once() -> None:
    async def scenario() -> None:
        repository = RecordingLifecycleRepository(active_aircraft())
        handler = RetireAircraftHandler(
            repository,
            clock=lambda: RETIRED_AT,
        )

        result = await handler.handle(RetireAircraftCommand(AIRCRAFT_ID))

        assert result.status is AircraftStatus.RETIRED
        assert result.retired_at == RETIRED_AT
        assert repository.update_calls == 1

    asyncio.run(scenario())


def test_retire_aircraft_is_idempotent_when_already_retired() -> None:
    async def scenario() -> None:
        aircraft = retired_aircraft()
        repository = RecordingLifecycleRepository(aircraft)
        clock_called = False

        def clock() -> datetime:
            nonlocal clock_called
            clock_called = True
            return datetime(2026, 11, 2, 12, 0, tzinfo=UTC)

        result = await RetireAircraftHandler(
            repository,
            clock=clock,
        ).handle(RetireAircraftCommand(AIRCRAFT_ID))

        assert result is aircraft
        assert result.retired_at == RETIRED_AT
        assert repository.update_calls == 0
        assert clock_called is False

    asyncio.run(scenario())


def test_retire_aircraft_returns_concurrent_retired_state() -> None:
    async def scenario() -> None:
        concurrent = retired_aircraft(retired_at=datetime(2026, 11, 1, 11, 30, tzinfo=UTC))
        repository = RecordingLifecycleRepository(
            active_aircraft(),
            conflict_on_update=True,
            concurrent_result=concurrent,
        )
        handler = RetireAircraftHandler(
            repository,
            clock=lambda: RETIRED_AT,
        )

        result = await handler.handle(RetireAircraftCommand(AIRCRAFT_ID))

        assert result is concurrent
        assert result.retired_at == datetime(2026, 11, 1, 11, 30, tzinfo=UTC)
        assert repository.update_calls == 1

    asyncio.run(scenario())


def test_retire_aircraft_raises_not_found_for_unknown_id() -> None:
    async def scenario() -> None:
        handler = RetireAircraftHandler(RecordingLifecycleRepository(None))

        with pytest.raises(AircraftNotFound, match=str(AIRCRAFT_ID)):
            await handler.handle(RetireAircraftCommand(AIRCRAFT_ID))

    asyncio.run(scenario())
