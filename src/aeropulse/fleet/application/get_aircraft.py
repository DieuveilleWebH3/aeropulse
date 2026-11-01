"""Get-aircraft application use case."""

from aeropulse.fleet.application.errors import AircraftNotFound
from aeropulse.fleet.application.queries import GetAircraftQuery
from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.repositories import AircraftReadRepository


class GetAircraftHandler:
    """Retrieve one aircraft by stable identifier."""

    def __init__(self, repository: AircraftReadRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetAircraftQuery) -> Aircraft:
        """Return the requested aircraft or raise AircraftNotFound."""
        aircraft = await self._repository.get_by_id(query.aircraft_id)
        if aircraft is None:
            raise AircraftNotFound(query.aircraft_id)
        return aircraft
