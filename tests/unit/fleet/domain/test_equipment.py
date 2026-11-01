"""Tests for Equipment domain values and aggregate behavior."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.errors import (
    InvalidEquipmentPartNumber,
    InvalidEquipmentSerialNumber,
    InvalidEquipmentType,
)
from aeropulse.fleet.domain.value_objects import (
    EquipmentPartNumber,
    EquipmentSerialNumber,
    EquipmentType,
)

EQUIPMENT_ID = UUID("11111111-2222-4333-8444-555555555555")
AIRCRAFT_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")


def test_equipment_type_is_canonicalized_but_manufacturer_ids_preserve_case() -> None:
    assert EquipmentType(" engine-control ").value == "ENGINE-CONTROL"
    assert EquipmentPartNumber("  PN-ab/01  ").value == "PN-ab/01"
    assert EquipmentSerialNumber("  Sn-00a  ").value == "Sn-00a"


@pytest.mark.parametrize(
    ("factory", "value", "error_type"),
    [
        (EquipmentType, "engine control", InvalidEquipmentType),
        (EquipmentPartNumber, "PN 001", InvalidEquipmentPartNumber),
        (EquipmentSerialNumber, "SN 001", InvalidEquipmentSerialNumber),
    ],
)
def test_equipment_value_objects_reject_unsupported_whitespace(
    factory: Callable[[str], object],
    value: str,
    error_type: type[ValueError],
) -> None:
    with pytest.raises(error_type):
        factory(value)


def test_equipment_normalizes_created_at_to_utc() -> None:
    source_timezone = timezone(timedelta(hours=2))
    equipment = Equipment(
        id=EQUIPMENT_ID,
        aircraft_id=AIRCRAFT_ID,
        equipment_type=EquipmentType("ENGINE"),
        part_number=EquipmentPartNumber("PN-001"),
        serial_number=EquipmentSerialNumber("SN-001"),
        created_at=datetime(2026, 11, 1, 12, 0, tzinfo=source_timezone),
    )

    assert equipment.created_at == datetime(2026, 11, 1, 10, 0, tzinfo=UTC)


def test_equipment_rejects_naive_created_at() -> None:
    with pytest.raises(ValueError, match="created_at must be timezone-aware"):
        Equipment(
            id=EQUIPMENT_ID,
            aircraft_id=AIRCRAFT_ID,
            equipment_type=EquipmentType("ENGINE"),
            part_number=EquipmentPartNumber("PN-001"),
            serial_number=EquipmentSerialNumber("SN-001"),
            created_at=datetime(2026, 11, 1, 10, 0),
        )
