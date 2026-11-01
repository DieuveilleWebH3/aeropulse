"""Domain errors for the Fleet bounded context."""


class FleetDomainError(Exception):
    """Base class for Fleet domain rule violations."""


class InvalidAircraftRegistration(FleetDomainError, ValueError):
    """Raised when an aircraft registration violates the AeroPulse V1 policy."""
