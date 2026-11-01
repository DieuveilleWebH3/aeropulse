"""Tests for the get-equipment application use case."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from aeropulse.fleet.application.errors import EquipmentNotFound
from aeropulse.fleet.application.get_equipment import GetEquipmentHandler
from aeropulse.fleet.application.queries import GetEquipmentQuery
from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.value_objects import (
    EquipmentPartNumber,
    EquipmentSerialNumber,
    EquipmentType,
)

EQUIPMENT_ID = UUID("11111111-2222-4333-8444-555555555555")
AIRCRAFT_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")


def equipment() -> Equipment:
    return Equipment(
        id=EQUIPMENT_ID,
        aircraft_id=AIRCRAFT_ID,
        equipment_type=EquipmentType("ENGINE-CONTROL"),
        part_number=EquipmentPartNumber("PN-001"),
        serial_number=EquipmentSerialNumber("SN-001"),
        created_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
    )


class StubRepository:
    def __init__(self, result: Equipment | None) -> None:
        self.result = result

    async def get_by_id(self, equipment_id: UUID) -> Equipment | None:
        assert equipment_id == EQUIPMENT_ID
        return self.result

    async def list_by_aircraft(
        self,
        aircraft_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Equipment]:
        raise AssertionError("list_by_aircraft must not be called")

    async def count_by_aircraft(self, aircraft_id: UUID) -> int:
        raise AssertionError("count_by_aircraft must not be called")


def test_get_equipment_returns_repository_result() -> None:
    async def scenario() -> None:
        expected = equipment()
        result = await GetEquipmentHandler(StubRepository(expected)).handle(
            GetEquipmentQuery(EQUIPMENT_ID)
        )
        assert result is expected

    asyncio.run(scenario())


def test_get_equipment_raises_not_found() -> None:
    async def scenario() -> None:
        with pytest.raises(EquipmentNotFound, match=str(EQUIPMENT_ID)):
            await GetEquipmentHandler(StubRepository(None)).handle(GetEquipmentQuery(EQUIPMENT_ID))

    asyncio.run(scenario())
