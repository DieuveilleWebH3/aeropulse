"""Tests for the list-equipment application use case."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest

from aeropulse.fleet.application.errors import AircraftNotFound
from aeropulse.fleet.application.list_equipment import ListEquipmentHandler
from aeropulse.fleet.application.queries import ListEquipmentQuery
from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.value_objects import (
    AircraftRegistration,
    EquipmentPartNumber,
    EquipmentSerialNumber,
    EquipmentType,
)

AIRCRAFT_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
EQUIPMENT_ID = UUID("11111111-2222-4333-8444-555555555555")


def aircraft() -> Aircraft:
    return Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=datetime(2026, 11, 1, 9, 0, tzinfo=UTC),
    )


def equipment() -> Equipment:
    return Equipment(
        id=EQUIPMENT_ID,
        aircraft_id=AIRCRAFT_ID,
        equipment_type=EquipmentType("ENGINE-CONTROL"),
        part_number=EquipmentPartNumber("PN-001"),
        serial_number=EquipmentSerialNumber("SN-001"),
        created_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
    )


class AircraftRepository:
    def __init__(self, result: Aircraft | None) -> None:
        self.result = result

    async def get_by_id(self, aircraft_id: UUID) -> Aircraft | None:
        assert aircraft_id == AIRCRAFT_ID
        return self.result

    async def list_aircraft(self, *, limit: int, offset: int) -> list[Aircraft]:
        raise AssertionError("list_aircraft must not be called")

    async def count_aircraft(self) -> int:
        raise AssertionError("count_aircraft must not be called")


class EquipmentRepository:
    def __init__(self) -> None:
        self.list_args: tuple[UUID, int, int] | None = None

    async def get_by_id(self, equipment_id: UUID) -> Equipment | None:
        raise AssertionError("get_by_id must not be called")

    async def list_by_aircraft(
        self,
        aircraft_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Equipment]:
        self.list_args = (aircraft_id, limit, offset)
        return [equipment()]

    async def count_by_aircraft(self, aircraft_id: UUID) -> int:
        assert aircraft_id == AIRCRAFT_ID
        return 1


def test_list_equipment_returns_page_for_existing_aircraft() -> None:
    async def scenario() -> None:
        equipment_repository = EquipmentRepository()
        handler = ListEquipmentHandler(
            equipment_repository,
            AircraftRepository(aircraft()),
        )

        page = await handler.handle(
            ListEquipmentQuery(
                aircraft_id=AIRCRAFT_ID,
                limit=25,
                offset=5,
            )
        )

        assert page.items == (equipment(),)
        assert page.total == 1
        assert page.limit == 25
        assert page.offset == 5
        assert equipment_repository.list_args == (AIRCRAFT_ID, 25, 5)

    asyncio.run(scenario())


def test_list_equipment_raises_for_unknown_aircraft() -> None:
    async def scenario() -> None:
        equipment_repository = EquipmentRepository()
        handler = ListEquipmentHandler(
            equipment_repository,
            AircraftRepository(None),
        )

        with pytest.raises(AircraftNotFound, match=str(AIRCRAFT_ID)):
            await handler.handle(ListEquipmentQuery(aircraft_id=AIRCRAFT_ID))

        assert equipment_repository.list_args is None

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("limit", "offset", "message"),
    [
        (0, 0, "equipment page limit"),
        (101, 0, "equipment page limit"),
        (50, -1, "equipment page offset"),
    ],
)
def test_list_equipment_query_rejects_invalid_pagination(
    limit: int,
    offset: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ListEquipmentQuery(
            aircraft_id=AIRCRAFT_ID,
            limit=limit,
            offset=offset,
        )
