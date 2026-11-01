"""Fleet application use cases."""

from aeropulse.fleet.application.commands import (
    RegisterAircraftCommand,
    RegisterEquipmentCommand,
    RetireAircraftCommand,
)
from aeropulse.fleet.application.errors import (
    AircraftNotFound,
    AircraftRegistrationAlreadyExists,
    AircraftRetiredForEquipmentRegistration,
    EquipmentAlreadyExists,
)
from aeropulse.fleet.application.get_aircraft import GetAircraftHandler
from aeropulse.fleet.application.list_aircraft import ListAircraftHandler
from aeropulse.fleet.application.queries import (
    AircraftPage,
    GetAircraftQuery,
    ListAircraftQuery,
)
from aeropulse.fleet.application.register_aircraft import RegisterAircraftHandler
from aeropulse.fleet.application.register_equipment import RegisterEquipmentHandler
from aeropulse.fleet.application.retire_aircraft import RetireAircraftHandler

__all__ = [
    "AircraftNotFound",
    "AircraftPage",
    "AircraftRegistrationAlreadyExists",
    "AircraftRetiredForEquipmentRegistration",
    "EquipmentAlreadyExists",
    "GetAircraftHandler",
    "GetAircraftQuery",
    "ListAircraftHandler",
    "ListAircraftQuery",
    "RegisterAircraftCommand",
    "RegisterAircraftHandler",
    "RegisterEquipmentCommand",
    "RegisterEquipmentHandler",
    "RetireAircraftCommand",
    "RetireAircraftHandler",
]
