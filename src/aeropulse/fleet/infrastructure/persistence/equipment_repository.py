"""SQLAlchemy implementation of Fleet equipment repository ports."""

from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, insert, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.repositories import EquipmentIdentityConflict
from aeropulse.fleet.domain.value_objects import (
    EquipmentPartNumber,
    EquipmentSerialNumber,
    EquipmentType,
)
from aeropulse.fleet.infrastructure.persistence.constraint_errors import (
    is_named_constraint_violation,
)
from aeropulse.fleet.infrastructure.persistence.schema import (
    EQUIPMENT_IDENTITY_UNIQUE_CONSTRAINT,
    equipment_table,
)


def _row_to_equipment(row: RowMapping) -> Equipment:
    return Equipment(
        id=cast(UUID, row["id"]),
        aircraft_id=cast(UUID, row["aircraft_id"]),
        equipment_type=EquipmentType(cast(str, row["equipment_type"])),
        part_number=EquipmentPartNumber(cast(str, row["part_number"])),
        serial_number=EquipmentSerialNumber(cast(str, row["serial_number"])),
        created_at=cast(datetime, row["created_at"]),
    )


class SqlAlchemyEquipmentRepository:
    """Persist and query Equipment using one caller-owned AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_by_identity(
        self,
        part_number: EquipmentPartNumber,
        serial_number: EquipmentSerialNumber,
    ) -> bool:
        statement = (
            select(equipment_table.c.id)
            .where(
                equipment_table.c.part_number == part_number.value,
                equipment_table.c.serial_number == serial_number.value,
            )
            .limit(1)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def add(self, equipment: Equipment) -> None:
        statement = insert(equipment_table).values(
            id=equipment.id,
            aircraft_id=equipment.aircraft_id,
            equipment_type=equipment.equipment_type.value,
            part_number=equipment.part_number.value,
            serial_number=equipment.serial_number.value,
            created_at=equipment.created_at,
        )
        try:
            await self._session.execute(statement)
        except IntegrityError as exc:
            if is_named_constraint_violation(
                exc,
                EQUIPMENT_IDENTITY_UNIQUE_CONSTRAINT,
            ):
                raise EquipmentIdentityConflict(
                    equipment.part_number,
                    equipment.serial_number,
                ) from exc
            raise

    async def get_by_id(self, equipment_id: UUID) -> Equipment | None:
        statement = select(equipment_table).where(equipment_table.c.id == equipment_id)
        result = await self._session.execute(statement)
        row = result.mappings().one_or_none()
        return None if row is None else _row_to_equipment(row)

    async def list_by_aircraft(
        self,
        aircraft_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Equipment]:
        statement = (
            select(equipment_table)
            .where(equipment_table.c.aircraft_id == aircraft_id)
            .order_by(
                equipment_table.c.created_at.asc(),
                equipment_table.c.id.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        return [_row_to_equipment(row) for row in result.mappings().all()]

    async def count_by_aircraft(self, aircraft_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(equipment_table)
            .where(equipment_table.c.aircraft_id == aircraft_id)
        )
        result = await self._session.execute(statement)
        return int(result.scalar_one())
