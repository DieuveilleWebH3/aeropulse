"""Register-equipment application use case."""

from collections.abc import Callable
from uuid import UUID, uuid4

from aeropulse.fleet.application.clock import Clock, utc_now
from aeropulse.fleet.application.commands import RegisterEquipmentCommand
from aeropulse.fleet.application.errors import (
    AircraftNotFound,
    AircraftRetiredForEquipmentRegistration,
    EquipmentAlreadyExists,
)
from aeropulse.fleet.domain.aircraft import AircraftStatus
from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.repositories import (
    AircraftEquipmentRegistrationRepository,
    EquipmentIdentityConflict,
    EquipmentRepository,
)
from aeropulse.fleet.domain.value_objects import (
    EquipmentPartNumber,
    EquipmentSerialNumber,
    EquipmentType,
)

type EquipmentIdGenerator = Callable[[], UUID]


class RegisterEquipmentHandler:
    """Register one equipment identity against an existing active aircraft."""

    def __init__(
        self,
        equipment_repository: EquipmentRepository,
        aircraft_repository: AircraftEquipmentRegistrationRepository,
        *,
        id_generator: EquipmentIdGenerator = uuid4,
        clock: Clock = utc_now,
    ) -> None:
        self._equipment_repository = equipment_repository
        self._aircraft_repository = aircraft_repository
        self._id_generator = id_generator
        self._clock = clock

    async def handle(self, command: RegisterEquipmentCommand) -> Equipment:
        """Validate, create, and persist one Equipment aggregate."""
        equipment_type = EquipmentType(command.equipment_type)
        part_number = EquipmentPartNumber(command.part_number)
        serial_number = EquipmentSerialNumber(command.serial_number)

        aircraft = await self._aircraft_repository.get_for_equipment_registration(
            command.aircraft_id
        )
        if aircraft is None:
            raise AircraftNotFound(command.aircraft_id)
        if aircraft.status is AircraftStatus.RETIRED:
            raise AircraftRetiredForEquipmentRegistration(command.aircraft_id)

        if await self._equipment_repository.exists_by_identity(
            part_number,
            serial_number,
        ):
            raise EquipmentAlreadyExists(part_number, serial_number)

        equipment = Equipment(
            id=self._id_generator(),
            aircraft_id=aircraft.id,
            equipment_type=equipment_type,
            part_number=part_number,
            serial_number=serial_number,
            created_at=self._clock(),
        )

        try:
            await self._equipment_repository.add(equipment)
        except EquipmentIdentityConflict as exc:
            raise EquipmentAlreadyExists(part_number, serial_number) from exc

        return equipment
