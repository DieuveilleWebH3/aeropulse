"""Repository ports owned by the Fleet domain."""

from typing import Protocol

from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.value_objects import AircraftRegistration


class AircraftRepository(Protocol):
    """Persistence contract required by Fleet application use cases."""

    async def exists_by_registration(self, registration: AircraftRegistration) -> bool:
        """Return whether the canonical registration already exists."""
        ...

    async def add(self, aircraft: Aircraft) -> None:
        """Persist a newly registered aircraft."""
        ...
