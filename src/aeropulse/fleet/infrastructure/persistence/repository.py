"""SQLAlchemy implementation of Fleet aircraft repository ports."""

from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, insert, select, update
from sqlalchemy.engine import CursorResult, RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.repositories import (
    AircraftRegistrationConflict,
    AircraftRetirementConflict,
)
from aeropulse.fleet.domain.value_objects import AircraftRegistration
from aeropulse.fleet.infrastructure.persistence.constraint_errors import (
    is_named_constraint_violation,
)
from aeropulse.fleet.infrastructure.persistence.schema import (
    AIRCRAFT_REGISTRATION_UNIQUE_CONSTRAINT,
    aircraft_table,
)


def _row_to_aircraft(row: RowMapping) -> Aircraft:
    """Rehydrate a domain Aircraft from one trusted database row."""
    return Aircraft.rehydrate(
        id=cast(UUID, row["id"]),
        registration=AircraftRegistration(cast(str, row["registration"])),
        status=AircraftStatus(cast(str, row["status"])),
        created_at=cast(datetime, row["created_at"]),
        retired_at=cast(datetime | None, row["retired_at"]),
    )


class SqlAlchemyAircraftRepository:
    """Persist and query Aircraft aggregates using one caller-owned AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_by_registration(
        self,
        registration: AircraftRegistration,
    ) -> bool:
        """Return whether the canonical registration is persisted."""
        statement = (
            select(aircraft_table.c.id)
            .where(aircraft_table.c.registration == registration.value)
            .limit(1)
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def add(self, aircraft: Aircraft) -> None:
        """Insert an Aircraft without committing the caller-owned transaction."""
        statement = insert(aircraft_table).values(
            id=aircraft.id,
            registration=aircraft.registration.value,
            status=aircraft.status.value,
            created_at=aircraft.created_at,
            retired_at=aircraft.retired_at,
        )

        try:
            await self._session.execute(statement)
        except IntegrityError as exc:
            if is_named_constraint_violation(
                exc,
                AIRCRAFT_REGISTRATION_UNIQUE_CONSTRAINT,
            ):
                raise AircraftRegistrationConflict(aircraft.registration) from exc
            raise

    async def get_by_id(self, aircraft_id: UUID) -> Aircraft | None:
        """Return one rehydrated Aircraft by identifier."""
        statement = select(aircraft_table).where(aircraft_table.c.id == aircraft_id)
        result = await self._session.execute(statement)
        row = result.mappings().one_or_none()
        return None if row is None else _row_to_aircraft(row)

    async def get_for_equipment_registration(
        self,
        aircraft_id: UUID,
    ) -> Aircraft | None:
        """Lock one aircraft row while equipment registration is decided."""
        statement = (
            select(aircraft_table).where(aircraft_table.c.id == aircraft_id).with_for_update()
        )
        result = await self._session.execute(statement)
        row = result.mappings().one_or_none()
        return None if row is None else _row_to_aircraft(row)

    async def list_aircraft(self, *, limit: int, offset: int) -> list[Aircraft]:
        """Return one deterministic aircraft page ordered by creation time and ID."""
        statement = (
            select(aircraft_table)
            .order_by(
                aircraft_table.c.created_at.asc(),
                aircraft_table.c.id.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        return [_row_to_aircraft(row) for row in result.mappings().all()]

    async def count_aircraft(self) -> int:
        """Return the total number of persisted aircraft."""
        statement = select(func.count()).select_from(aircraft_table)
        result = await self._session.execute(statement)
        return int(result.scalar_one())

    async def update_retirement(self, aircraft: Aircraft) -> None:
        """Persist one conditional ACTIVE -> RETIRED transition."""
        if aircraft.status is not AircraftStatus.RETIRED or aircraft.retired_at is None:
            raise ValueError("retirement persistence requires a retired aircraft")

        statement = (
            update(aircraft_table)
            .where(
                aircraft_table.c.id == aircraft.id,
                aircraft_table.c.status == AircraftStatus.ACTIVE.value,
                aircraft_table.c.retired_at.is_(None),
            )
            .values(
                status=AircraftStatus.RETIRED.value,
                retired_at=aircraft.retired_at,
            )
        )
        result = cast(
            CursorResult[Any],
            await self._session.execute(statement),
        )
        if result.rowcount != 1:
            raise AircraftRetirementConflict(aircraft.id)
