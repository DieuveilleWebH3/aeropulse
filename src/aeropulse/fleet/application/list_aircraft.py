"""List-aircraft application use case."""

from aeropulse.fleet.application.queries import AircraftPage, ListAircraftQuery
from aeropulse.fleet.domain.repositories import AircraftReadRepository


class ListAircraftHandler:
    """Return a deterministic paginated view of Fleet aircraft."""

    def __init__(self, repository: AircraftReadRepository) -> None:
        self._repository = repository

    async def handle(self, query: ListAircraftQuery) -> AircraftPage:
        """Return one aircraft page plus the current total count."""
        items = await self._repository.list_aircraft(
            limit=query.limit,
            offset=query.offset,
        )
        total = await self._repository.count_aircraft()
        return AircraftPage(
            items=tuple(items),
            total=total,
            limit=query.limit,
            offset=query.offset,
        )
