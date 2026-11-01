"""List-equipment application use case."""

from aeropulse.fleet.application.errors import AircraftNotFound
from aeropulse.fleet.application.queries import EquipmentPage, ListEquipmentQuery
from aeropulse.fleet.domain.repositories import (
    AircraftReadRepository,
    EquipmentReadRepository,
)


class ListEquipmentHandler:
    """Return a deterministic equipment page for one existing aircraft."""

    def __init__(
        self,
        equipment_repository: EquipmentReadRepository,
        aircraft_repository: AircraftReadRepository,
    ) -> None:
        self._equipment_repository = equipment_repository
        self._aircraft_repository = aircraft_repository

    async def handle(self, query: ListEquipmentQuery) -> EquipmentPage:
        """Return one equipment page or fail when the parent aircraft is missing."""
        aircraft = await self._aircraft_repository.get_by_id(query.aircraft_id)
        if aircraft is None:
            raise AircraftNotFound(query.aircraft_id)

        items = await self._equipment_repository.list_by_aircraft(
            query.aircraft_id,
            limit=query.limit,
            offset=query.offset,
        )
        total = await self._equipment_repository.count_by_aircraft(query.aircraft_id)

        return EquipmentPage(
            items=tuple(items),
            total=total,
            limit=query.limit,
            offset=query.offset,
        )
