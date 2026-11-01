"""Tests for the register-equipment use case."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import pytest

from aeropulse.fleet.application.commands import RegisterEquipmentCommand
from aeropulse.fleet.application.errors import (
    AircraftNotFound,
    AircraftRetiredForEquipmentRegistration,
    EquipmentAlreadyExists,
)
from aeropulse.fleet.application.register_equipment import RegisterEquipmentHandler
from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.repositories import EquipmentIdentityConflict
from aeropulse.fleet.domain.value_objects import (
    AircraftRegistration,
    EquipmentPartNumber,
    EquipmentSerialNumber,
)

AIRCRAFT_ID = UUID("10000000-0000-4000-8000-000000000001")
EQUIPMENT_ID = UUID("20000000-0000-4000-8000-000000000001")
CREATED_AT = datetime(2026, 11, 1, 14, 0, tzinfo=UTC)


def active_aircraft() -> Aircraft:
    return Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
    )


def retired_aircraft() -> Aircraft:
    return Aircraft.rehydrate(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        status=AircraftStatus.RETIRED,
        created_at=datetime(2026, 11, 1, 10, 0, tzinfo=UTC),
        retired_at=datetime(2026, 11, 1, 12, 0, tzinfo=UTC),
    )


@dataclass
class AircraftRegistrationRepositoryStub:
    aircraft: Aircraft | None
    calls: int = 0

    async def get_for_equipment_registration(self, aircraft_id: UUID) -> Aircraft | None:
        self.calls += 1
        if self.aircraft is not None and self.aircraft.id == aircraft_id:
            return self.aircraft
        return None


@dataclass
class EquipmentRepositoryStub:
    duplicate: bool = False
    conflict_on_add: bool = False
    identity_checks: list[tuple[EquipmentPartNumber, EquipmentSerialNumber]] = field(
        default_factory=list
    )
    added: list[Equipment] = field(default_factory=list)

    async def exists_by_identity(
        self,
        part_number: EquipmentPartNumber,
        serial_number: EquipmentSerialNumber,
    ) -> bool:
        self.identity_checks.append((part_number, serial_number))
        return self.duplicate

    async def add(self, equipment: Equipment) -> None:
        if self.conflict_on_add:
            raise EquipmentIdentityConflict(equipment.part_number, equipment.serial_number)
        self.added.append(equipment)


def command() -> RegisterEquipmentCommand:
    return RegisterEquipmentCommand(
        aircraft_id=AIRCRAFT_ID,
        equipment_type=" engine-control ",
        part_number=" PN-ab/01 ",
        serial_number=" Sn-00a ",
    )


def test_register_equipment_creates_deterministic_equipment() -> None:
    async def scenario() -> None:
        aircraft_repository = AircraftRegistrationRepositoryStub(active_aircraft())
        equipment_repository = EquipmentRepositoryStub()
        handler = RegisterEquipmentHandler(
            equipment_repository,
            aircraft_repository,
            id_generator=lambda: EQUIPMENT_ID,
            clock=lambda: CREATED_AT,
        )

        equipment = await handler.handle(command())

        assert equipment.id == EQUIPMENT_ID
        assert equipment.aircraft_id == AIRCRAFT_ID
        assert equipment.equipment_type.value == "ENGINE-CONTROL"
        assert equipment.part_number.value == "PN-ab/01"
        assert equipment.serial_number.value == "Sn-00a"
        assert equipment.created_at == CREATED_AT
        assert equipment_repository.added == [equipment]

    asyncio.run(scenario())


def test_register_equipment_rejects_unknown_aircraft() -> None:
    async def scenario() -> None:
        handler = RegisterEquipmentHandler(
            EquipmentRepositoryStub(),
            AircraftRegistrationRepositoryStub(None),
        )
        with pytest.raises(AircraftNotFound, match=str(AIRCRAFT_ID)):
            await handler.handle(command())

    asyncio.run(scenario())


def test_register_equipment_rejects_retired_aircraft() -> None:
    async def scenario() -> None:
        equipment_repository = EquipmentRepositoryStub()
        handler = RegisterEquipmentHandler(
            equipment_repository,
            AircraftRegistrationRepositoryStub(retired_aircraft()),
        )
        with pytest.raises(AircraftRetiredForEquipmentRegistration):
            await handler.handle(command())
        assert equipment_repository.identity_checks == []

    asyncio.run(scenario())


def test_register_equipment_rejects_known_identity() -> None:
    async def scenario() -> None:
        handler = RegisterEquipmentHandler(
            EquipmentRepositoryStub(duplicate=True),
            AircraftRegistrationRepositoryStub(active_aircraft()),
        )
        with pytest.raises(EquipmentAlreadyExists, match="PN-ab/01/Sn-00a"):
            await handler.handle(command())

    asyncio.run(scenario())


def test_register_equipment_translates_late_unique_conflict() -> None:
    async def scenario() -> None:
        handler = RegisterEquipmentHandler(
            EquipmentRepositoryStub(conflict_on_add=True),
            AircraftRegistrationRepositoryStub(active_aircraft()),
            id_generator=lambda: EQUIPMENT_ID,
            clock=lambda: CREATED_AT,
        )
        with pytest.raises(EquipmentAlreadyExists, match="PN-ab/01/Sn-00a"):
            await handler.handle(command())

    asyncio.run(scenario())
