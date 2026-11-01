"""Tests for Aircraft retirement lifecycle behavior."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.value_objects import AircraftRegistration

AIRCRAFT_ID = UUID("88888888-8888-4888-8888-888888888888")
CREATED_AT = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)


def build_aircraft() -> Aircraft:
    return Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=CREATED_AT,
    )


def test_retire_transitions_active_aircraft_and_normalizes_time() -> None:
    aircraft = build_aircraft()
    source_timezone = timezone(timedelta(hours=1))

    changed = aircraft.retire(retired_at=datetime(2026, 11, 1, 13, 0, tzinfo=source_timezone))

    assert changed is True
    assert aircraft.status is AircraftStatus.RETIRED
    assert aircraft.retired_at == datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def test_retire_is_idempotent_and_preserves_original_timestamp() -> None:
    aircraft = build_aircraft()
    first_retired_at = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)

    assert aircraft.retire(retired_at=first_retired_at) is True
    assert aircraft.retire(retired_at=datetime(2026, 11, 2, 12, 0, tzinfo=UTC)) is False

    assert aircraft.retired_at == first_retired_at


def test_retire_rejects_naive_timestamp() -> None:
    aircraft = build_aircraft()

    with pytest.raises(ValueError, match="retired_at must be timezone-aware"):
        aircraft.retire(retired_at=datetime(2026, 11, 1, 12, 0))


def test_retire_rejects_timestamp_before_registration() -> None:
    aircraft = build_aircraft()

    with pytest.raises(ValueError, match="must not precede created_at"):
        aircraft.retire(retired_at=datetime(2026, 11, 1, 9, 59, tzinfo=UTC))
