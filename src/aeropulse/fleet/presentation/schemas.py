"""HTTP schemas for Fleet aircraft APIs."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aeropulse.fleet.application.queries import AircraftPage, EquipmentPage
from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.equipment import Equipment


class RegisterAircraftRequest(BaseModel):
    """HTTP request body for aircraft registration."""

    model_config = ConfigDict(extra="forbid")

    registration: str


class AircraftResponse(BaseModel):
    """HTTP representation of an Aircraft aggregate."""

    id: UUID
    registration: str
    status: AircraftStatus
    created_at: datetime
    retired_at: datetime | None

    @classmethod
    def from_domain(cls, aircraft: Aircraft) -> Self:
        """Map a domain Aircraft to the public HTTP contract."""
        return cls(
            id=aircraft.id,
            registration=aircraft.registration.value,
            status=aircraft.status,
            created_at=aircraft.created_at,
            retired_at=aircraft.retired_at,
        )


class AircraftListResponse(BaseModel):
    """Paginated HTTP representation of Fleet aircraft."""

    items: list[AircraftResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_application(cls, page: AircraftPage) -> Self:
        """Map an application aircraft page to the HTTP contract."""
        return cls(
            items=[AircraftResponse.from_domain(aircraft) for aircraft in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )


class RegisterEquipmentRequest(BaseModel):
    """HTTP request body for equipment registration."""

    model_config = ConfigDict(extra="forbid")

    equipment_type: str
    part_number: str
    serial_number: str


class EquipmentResponse(BaseModel):
    """HTTP representation of an Equipment aggregate."""

    id: UUID
    aircraft_id: UUID
    equipment_type: str
    part_number: str
    serial_number: str
    created_at: datetime

    @classmethod
    def from_domain(cls, equipment: Equipment) -> Self:
        """Map a domain Equipment to the public HTTP contract."""
        return cls(
            id=equipment.id,
            aircraft_id=equipment.aircraft_id,
            equipment_type=equipment.equipment_type.value,
            part_number=equipment.part_number.value,
            serial_number=equipment.serial_number.value,
            created_at=equipment.created_at,
        )


class EquipmentListResponse(BaseModel):
    """Paginated HTTP representation of aircraft equipment."""

    items: list[EquipmentResponse]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_application(cls, page: EquipmentPage) -> Self:
        """Map an application equipment page to the HTTP contract."""
        return cls(
            items=[EquipmentResponse.from_domain(item) for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )


class ApiErrorDetail(BaseModel):
    """Stable machine-readable API error details."""

    code: str
    message: str
    field: str | None = None


class ApiErrorResponse(BaseModel):
    """Public error envelope."""

    error: ApiErrorDetail
