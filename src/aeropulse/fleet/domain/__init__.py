"""Fleet domain model."""

from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.errors import InvalidAircraftRegistration
from aeropulse.fleet.domain.value_objects import AircraftRegistration

__all__ = [
    "Aircraft",
    "AircraftRegistration",
    "AircraftStatus",
    "InvalidAircraftRegistration",
]
