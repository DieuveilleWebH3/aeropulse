"""Domain errors for the Fleet bounded context."""


class FleetDomainError(Exception):
    """Base class for Fleet domain rule violations."""


class InvalidAircraftRegistration(FleetDomainError, ValueError):
    """Raised when an aircraft registration violates the AeroPulse V1 policy."""


class InvalidEquipmentType(FleetDomainError, ValueError):
    """Raised when an equipment type violates the AeroPulse V1 policy."""


class InvalidEquipmentPartNumber(FleetDomainError, ValueError):
    """Raised when an equipment part number violates the AeroPulse V1 policy."""


class InvalidEquipmentSerialNumber(FleetDomainError, ValueError):
    """Raised when an equipment serial number violates the AeroPulse V1 policy."""
