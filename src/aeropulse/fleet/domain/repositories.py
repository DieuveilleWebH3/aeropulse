"""Repository ports owned by the Fleet domain."""

from typing import Protocol
from uuid import UUID

from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.value_objects import (
    AircraftRegistration,
    EquipmentPartNumber,
    EquipmentSerialNumber,
)


class AircraftRegistrationConflict(Exception):
    """Raised when persistence cannot preserve registration uniqueness."""

    def __init__(self, registration: AircraftRegistration) -> None:
        self.registration = registration
        super().__init__(f"aircraft registration conflicts with persisted data: {registration}")


class AircraftRetirementConflict(Exception):
    """Raised when persistence loses the expected ACTIVE retirement precondition."""

    def __init__(self, aircraft_id: UUID) -> None:
        self.aircraft_id = aircraft_id
        super().__init__(f"aircraft retirement state changed concurrently: {aircraft_id}")


class AircraftRepository(Protocol):
    """Persistence contract required by aircraft-registration use cases."""

    async def exists_by_registration(self, registration: AircraftRegistration) -> bool:
        """Return whether the canonical registration already exists."""
        ...

    async def add(self, aircraft: Aircraft) -> None:
        """Persist a newly registered aircraft.

        Raises:
            AircraftRegistrationConflict: if persistence detects a concurrent
                registration uniqueness conflict.
        """
        ...


class AircraftReadRepository(Protocol):
    """Read contract required by Fleet aircraft query use cases."""

    async def get_by_id(self, aircraft_id: UUID) -> Aircraft | None:
        """Return one aircraft by stable identifier, if present."""
        ...

    async def list_aircraft(self, *, limit: int, offset: int) -> list[Aircraft]:
        """Return one deterministic page of aircraft."""
        ...

    async def count_aircraft(self) -> int:
        """Return the total number of persisted aircraft."""
        ...


class AircraftLifecycleRepository(Protocol):
    """Persistence contract required by aircraft lifecycle use cases."""

    async def get_by_id(self, aircraft_id: UUID) -> Aircraft | None:
        """Return one aircraft by stable identifier, if present."""
        ...

    async def update_retirement(self, aircraft: Aircraft) -> None:
        """Persist one ACTIVE -> RETIRED transition conditionally.

        Raises:
            AircraftRetirementConflict: if the persisted aircraft is no longer ACTIVE.
        """
        ...


class EquipmentIdentityConflict(Exception):
    """Raised when persistence cannot preserve equipment natural identity."""

    def __init__(
        self,
        part_number: EquipmentPartNumber,
        serial_number: EquipmentSerialNumber,
    ) -> None:
        self.part_number = part_number
        self.serial_number = serial_number
        super().__init__(
            f"equipment identity conflicts with persisted data: {part_number}/{serial_number}"
        )


class AircraftEquipmentRegistrationRepository(Protocol):
    """Aircraft access needed while registering equipment."""

    async def get_for_equipment_registration(self, aircraft_id: UUID) -> Aircraft | None:
        """Return and lock an aircraft row for equipment-registration serialization."""
        ...


class EquipmentRepository(Protocol):
    """Persistence contract required by equipment-registration use cases."""

    async def exists_by_identity(
        self,
        part_number: EquipmentPartNumber,
        serial_number: EquipmentSerialNumber,
    ) -> bool:
        """Return whether the part-number/serial-number pair already exists."""
        ...

    async def add(self, equipment: Equipment) -> None:
        """Persist newly registered equipment.

        Raises:
            EquipmentIdentityConflict: if a competing insert wins the identity race.
        """
        ...


class EquipmentReadRepository(Protocol):
    """Read contract prepared for the S1-007 Equipment HTTP API."""

    async def get_by_id(self, equipment_id: UUID) -> Equipment | None: ...

    async def list_by_aircraft(
        self,
        aircraft_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Equipment]: ...

    async def count_by_aircraft(self, aircraft_id: UUID) -> int: ...
