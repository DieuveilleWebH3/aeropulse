"""Register-aircraft application use case."""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from aeropulse.fleet.application.commands import RegisterAircraftCommand
from aeropulse.fleet.application.errors import AircraftRegistrationAlreadyExists
from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.repositories import AircraftRepository
from aeropulse.fleet.domain.value_objects import AircraftRegistration

type AircraftIdGenerator = Callable[[], UUID]
type Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(UTC)


class RegisterAircraftHandler:
    """Register a new aircraft while preserving Fleet registration invariants."""

    def __init__(
        self,
        repository: AircraftRepository,
        *,
        id_generator: AircraftIdGenerator = uuid4,
        clock: Clock = utc_now,
    ) -> None:
        self._repository = repository
        self._id_generator = id_generator
        self._clock = clock

    async def handle(self, command: RegisterAircraftCommand) -> Aircraft:
        """Register one aircraft and return the created aggregate."""
        registration = AircraftRegistration(command.registration)

        if await self._repository.exists_by_registration(registration):
            raise AircraftRegistrationAlreadyExists(registration)

        aircraft = Aircraft(
            id=self._id_generator(),
            registration=registration,
            created_at=self._clock(),
        )
        await self._repository.add(aircraft)
        return aircraft
