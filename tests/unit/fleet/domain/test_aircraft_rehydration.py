"""Tests for restoring Aircraft aggregates from persisted state."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.value_objects import AircraftRegistration

AIRCRAFT_ID = UUID("44444444-4444-4444-8444-444444444444")


def test_rehydrate_restores_retired_status_and_normalizes_time_to_utc() -> None:
    source_timezone = timezone(timedelta(hours=1))

    aircraft = Aircraft.rehydrate(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        status=AircraftStatus.RETIRED,
        created_at=datetime(2026, 11, 1, 11, 0, tzinfo=source_timezone),
    )

    assert aircraft.id == AIRCRAFT_ID
    assert aircraft.registration == AircraftRegistration("F-HABC")
    assert aircraft.status is AircraftStatus.RETIRED
    assert aircraft.created_at == datetime(2026, 11, 1, 10, 0, tzinfo=UTC)
