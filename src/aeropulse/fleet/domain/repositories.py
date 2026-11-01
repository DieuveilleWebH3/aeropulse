"""Repository ports owned by the Fleet domain."""

from typing import Protocol
from uuid import UUID

from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.value_objects import AircraftRegistration


class AircraftRegistrationConflict(Exception):
    """Raised when persistence cannot preserve registration uniqueness."""

    def __init__(self, registration: AircraftRegistration) -> None:
        self.registration = registration
        super().__init__(f"aircraft registration conflicts with persisted data: {registration}")


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
