"""Register-aircraft application use case."""

from collections.abc import Callable
from uuid import UUID, uuid4

from aeropulse.fleet.application.clock import Clock, utc_now
from aeropulse.fleet.application.commands import RegisterAircraftCommand
from aeropulse.fleet.application.errors import AircraftRegistrationAlreadyExists
from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.repositories import AircraftRegistrationConflict, AircraftRepository
from aeropulse.fleet.domain.value_objects import AircraftRegistration

type AircraftIdGenerator = Callable[[], UUID]


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
        try:
            await self._repository.add(aircraft)
        except AircraftRegistrationConflict as exc:
            raise AircraftRegistrationAlreadyExists(registration) from exc

        return aircraft
