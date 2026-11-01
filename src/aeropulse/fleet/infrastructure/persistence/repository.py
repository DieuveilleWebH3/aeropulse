"""SQLAlchemy implementation of the Fleet aircraft repository port."""

from collections.abc import Iterator

from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.repositories import (
    AircraftRegistrationConflict,
)
from aeropulse.fleet.domain.value_objects import AircraftRegistration
from aeropulse.fleet.infrastructure.persistence.schema import (
    AIRCRAFT_REGISTRATION_UNIQUE_CONSTRAINT,
    aircraft_table,
)


def _exception_chain(exc: BaseException) -> Iterator[BaseException]:
    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _is_registration_unique_violation(exc: IntegrityError) -> bool:
    return any(
        getattr(item, "constraint_name", None) == AIRCRAFT_REGISTRATION_UNIQUE_CONSTRAINT
        for item in _exception_chain(exc)
    )


class SqlAlchemyAircraftRepository:
    """Persist Aircraft aggregates using one caller-owned AsyncSession."""

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
        )

        try:
            await self._session.execute(statement)
        except IntegrityError as exc:
            if _is_registration_unique_violation(exc):
                raise AircraftRegistrationConflict(aircraft.registration) from exc
            raise
