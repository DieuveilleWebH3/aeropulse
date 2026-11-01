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
    EquipmentNotFound,
)
from aeropulse.fleet.application.get_aircraft import GetAircraftHandler
from aeropulse.fleet.application.get_equipment import GetEquipmentHandler
from aeropulse.fleet.application.list_aircraft import ListAircraftHandler
from aeropulse.fleet.application.list_equipment import ListEquipmentHandler
from aeropulse.fleet.application.queries import (
    AircraftPage,
    EquipmentPage,
    GetAircraftQuery,
    GetEquipmentQuery,
    ListAircraftQuery,
    ListEquipmentQuery,
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
    "EquipmentNotFound",
    "EquipmentPage",
    "GetAircraftHandler",
    "GetAircraftQuery",
    "GetEquipmentHandler",
    "GetEquipmentQuery",
    "ListAircraftHandler",
    "ListAircraftQuery",
    "ListEquipmentHandler",
    "ListEquipmentQuery",
    "RegisterAircraftCommand",
    "RegisterAircraftHandler",
    "RegisterEquipmentCommand",
    "RegisterEquipmentHandler",
    "RetireAircraftCommand",
    "RetireAircraftHandler",
]
