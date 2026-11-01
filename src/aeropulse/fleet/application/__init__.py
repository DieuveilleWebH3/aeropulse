"""Fleet application use cases."""

from aeropulse.fleet.application.commands import RegisterAircraftCommand
from aeropulse.fleet.application.errors import (
    AircraftNotFound,
    AircraftRegistrationAlreadyExists,
)
from aeropulse.fleet.application.get_aircraft import GetAircraftHandler
from aeropulse.fleet.application.list_aircraft import ListAircraftHandler
from aeropulse.fleet.application.queries import (
    AircraftPage,
    GetAircraftQuery,
    ListAircraftQuery,
)
from aeropulse.fleet.application.register_aircraft import RegisterAircraftHandler

__all__ = [
    "AircraftNotFound",
    "AircraftPage",
    "AircraftRegistrationAlreadyExists",
    "GetAircraftHandler",
    "GetAircraftQuery",
    "ListAircraftHandler",
    "ListAircraftQuery",
    "RegisterAircraftCommand",
    "RegisterAircraftHandler",
]
