"""Commands handled by the Fleet application layer."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisterAircraftCommand:
    """Request to register one aircraft."""

    registration: str


@dataclass(frozen=True, slots=True)
class RetireAircraftCommand:
    """Request to retire one aircraft."""

    aircraft_id: UUID


@dataclass(frozen=True, slots=True)
class RegisterEquipmentCommand:
    """Request to register equipment against one active aircraft."""

    aircraft_id: UUID
    equipment_type: str
    part_number: str
    serial_number: str
