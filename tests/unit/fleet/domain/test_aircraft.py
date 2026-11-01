"""Tests for the Aircraft aggregate root."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.value_objects import AircraftRegistration

AIRCRAFT_ID = UUID("11111111-1111-4111-8111-111111111111")


def test_new_aircraft_is_active() -> None:
    aircraft = Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=datetime(2026, 11, 1, 8, 30, tzinfo=UTC),
    )

    assert aircraft.status is AircraftStatus.ACTIVE


def test_aircraft_created_at_is_normalized_to_utc() -> None:
    paris_like_offset = timezone(timedelta(hours=1))
    aircraft = Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=datetime(2026, 11, 1, 9, 30, tzinfo=paris_like_offset),
    )

    assert aircraft.created_at == datetime(2026, 11, 1, 8, 30, tzinfo=UTC)
    assert aircraft.created_at.tzinfo is UTC


def test_aircraft_rejects_naive_created_at() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        Aircraft(
            id=AIRCRAFT_ID,
            registration=AircraftRegistration("F-HABC"),
            created_at=datetime(2026, 11, 1, 8, 30),
        )


def test_aircraft_registration_cannot_be_reassigned() -> None:
    aircraft = Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=datetime(2026, 11, 1, 8, 30, tzinfo=UTC),
    )

    attribute_name = "registration"

    with pytest.raises(AttributeError):
        setattr(aircraft, attribute_name, AircraftRegistration("N123AB"))
