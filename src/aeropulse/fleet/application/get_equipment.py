"""Get-equipment application use case."""

from aeropulse.fleet.application.errors import EquipmentNotFound
from aeropulse.fleet.application.queries import GetEquipmentQuery
from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.repositories import EquipmentReadRepository


class GetEquipmentHandler:
    """Retrieve one equipment item by stable identifier."""

    def __init__(self, repository: EquipmentReadRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetEquipmentQuery) -> Equipment:
        """Return the requested equipment or raise EquipmentNotFound."""
        equipment = await self._repository.get_by_id(query.equipment_id)
        if equipment is None:
            raise EquipmentNotFound(query.equipment_id)
        return equipment
