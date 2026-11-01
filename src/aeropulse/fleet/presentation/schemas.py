"""HTTP schemas for Fleet aircraft APIs."""

from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aeropulse.fleet.application.queries import AircraftPage
from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus


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


class ApiErrorDetail(BaseModel):
    """Stable machine-readable API error details."""

    code: str
    message: str
    field: str | None = None


class ApiErrorResponse(BaseModel):
    """Public error envelope."""

    error: ApiErrorDetail
