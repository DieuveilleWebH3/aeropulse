"""Application-level errors for Fleet use cases."""

from aeropulse.fleet.domain.value_objects import AircraftRegistration


class FleetApplicationError(Exception):
    """Base class for Fleet application failures."""


class AircraftRegistrationAlreadyExists(FleetApplicationError):
    """Raised when a registration is already known to the Fleet context."""

    def __init__(self, registration: AircraftRegistration) -> None:
        self.registration = registration
        super().__init__(f"aircraft registration already exists: {registration}")
