"""Retire-aircraft application use case."""

from aeropulse.fleet.application.clock import Clock, utc_now
from aeropulse.fleet.application.commands import RetireAircraftCommand
from aeropulse.fleet.application.errors import AircraftNotFound
from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.repositories import (
    AircraftLifecycleRepository,
    AircraftRetirementConflict,
)


class RetireAircraftHandler:
    """Apply an idempotent ACTIVE -> RETIRED aircraft lifecycle transition."""

    def __init__(
        self,
        repository: AircraftLifecycleRepository,
        *,
        clock: Clock = utc_now,
    ) -> None:
        self._repository = repository
        self._clock = clock

    async def handle(self, command: RetireAircraftCommand) -> Aircraft:
        """Retire the requested aircraft and return its current aggregate."""
        aircraft = await self._repository.get_by_id(command.aircraft_id)
        if aircraft is None:
            raise AircraftNotFound(command.aircraft_id)

        if aircraft.status is AircraftStatus.RETIRED:
            return aircraft

        aircraft.retire(retired_at=self._clock())

        try:
            await self._repository.update_retirement(aircraft)
        except AircraftRetirementConflict as exc:
            current = await self._repository.get_by_id(command.aircraft_id)
            if current is None:
                raise AircraftNotFound(command.aircraft_id) from exc
            if current.status is AircraftStatus.RETIRED:
                return current
            raise

        return aircraft
