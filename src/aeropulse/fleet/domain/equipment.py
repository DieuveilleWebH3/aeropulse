"""Equipment aggregate owned by the Fleet bounded context."""

from datetime import UTC, datetime
from uuid import UUID

from aeropulse.fleet.domain.value_objects import (
    EquipmentPartNumber,
    EquipmentSerialNumber,
    EquipmentType,
)


def _normalize_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("equipment created_at must be timezone-aware")
    return value.astimezone(UTC)


class Equipment:
    """Maintainable equipment currently associated with one aircraft."""

    __slots__ = (
        "_aircraft_id",
        "_created_at",
        "_equipment_type",
        "_id",
        "_part_number",
        "_serial_number",
    )

    def __init__(
        self,
        *,
        id: UUID,
        aircraft_id: UUID,
        equipment_type: EquipmentType,
        part_number: EquipmentPartNumber,
        serial_number: EquipmentSerialNumber,
        created_at: datetime,
    ) -> None:
        self._id = id
        self._aircraft_id = aircraft_id
        self._equipment_type = equipment_type
        self._part_number = part_number
        self._serial_number = serial_number
        self._created_at = _normalize_aware_datetime(created_at)

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def aircraft_id(self) -> UUID:
        return self._aircraft_id

    @property
    def equipment_type(self) -> EquipmentType:
        return self._equipment_type

    @property
    def part_number(self) -> EquipmentPartNumber:
        return self._part_number

    @property
    def serial_number(self) -> EquipmentSerialNumber:
        return self._serial_number

    @property
    def created_at(self) -> datetime:
        return self._created_at
