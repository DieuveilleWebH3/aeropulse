"""FastAPI dependency composition for Fleet use cases."""

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.api.runtime import RuntimeResources
from aeropulse.fleet.application.get_aircraft import GetAircraftHandler
from aeropulse.fleet.application.get_equipment import GetEquipmentHandler
from aeropulse.fleet.application.list_aircraft import ListAircraftHandler
from aeropulse.fleet.application.list_equipment import ListEquipmentHandler
from aeropulse.fleet.application.register_aircraft import RegisterAircraftHandler
from aeropulse.fleet.application.register_equipment import RegisterEquipmentHandler
from aeropulse.fleet.application.retire_aircraft import RetireAircraftHandler
from aeropulse.fleet.infrastructure.persistence.equipment_repository import (
    SqlAlchemyEquipmentRepository,
)
from aeropulse.fleet.infrastructure.persistence.repository import SqlAlchemyAircraftRepository


async def get_database_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide one transaction-scoped AsyncSession for a request use case."""
    resources = cast(
        RuntimeResources | None,
        getattr(request.app.state, "runtime_resources", None),
    )
    if resources is None:
        raise RuntimeError("application runtime resources are not initialized")

    session = resources.create_database_session()
    async with session, session.begin():
        yield session


type DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session, scope="function"),
]


def get_register_aircraft_handler(session: DatabaseSession) -> RegisterAircraftHandler:
    """Compose the aircraft-registration use case for one transaction."""
    repository = SqlAlchemyAircraftRepository(session)
    return RegisterAircraftHandler(repository)


def get_aircraft_handler(session: DatabaseSession) -> GetAircraftHandler:
    """Compose the get-aircraft use case for one transaction."""
    repository = SqlAlchemyAircraftRepository(session)
    return GetAircraftHandler(repository)


def get_list_aircraft_handler(session: DatabaseSession) -> ListAircraftHandler:
    """Compose the list-aircraft use case for one transaction."""
    repository = SqlAlchemyAircraftRepository(session)
    return ListAircraftHandler(repository)


def get_retire_aircraft_handler(session: DatabaseSession) -> RetireAircraftHandler:
    """Compose the retire-aircraft use case for one transaction."""
    repository = SqlAlchemyAircraftRepository(session)
    return RetireAircraftHandler(repository)


def get_register_equipment_handler(
    session: DatabaseSession,
) -> RegisterEquipmentHandler:
    """Compose the equipment-registration use case for one transaction."""
    equipment_repository = SqlAlchemyEquipmentRepository(session)
    aircraft_repository = SqlAlchemyAircraftRepository(session)
    return RegisterEquipmentHandler(
        equipment_repository,
        aircraft_repository,
    )


def get_equipment_handler(session: DatabaseSession) -> GetEquipmentHandler:
    """Compose the get-equipment use case for one transaction."""
    repository = SqlAlchemyEquipmentRepository(session)
    return GetEquipmentHandler(repository)


def get_list_equipment_handler(session: DatabaseSession) -> ListEquipmentHandler:
    """Compose the list-equipment use case for one transaction."""
    equipment_repository = SqlAlchemyEquipmentRepository(session)
    aircraft_repository = SqlAlchemyAircraftRepository(session)
    return ListEquipmentHandler(
        equipment_repository,
        aircraft_repository,
    )


type RegisterAircraftHandlerDependency = Annotated[
    RegisterAircraftHandler,
    Depends(get_register_aircraft_handler),
]

type GetAircraftHandlerDependency = Annotated[
    GetAircraftHandler,
    Depends(get_aircraft_handler),
]

type ListAircraftHandlerDependency = Annotated[
    ListAircraftHandler,
    Depends(get_list_aircraft_handler),
]


type RetireAircraftHandlerDependency = Annotated[
    RetireAircraftHandler,
    Depends(get_retire_aircraft_handler),
]


type RegisterEquipmentHandlerDependency = Annotated[
    RegisterEquipmentHandler,
    Depends(get_register_equipment_handler),
]

type GetEquipmentHandlerDependency = Annotated[
    GetEquipmentHandler,
    Depends(get_equipment_handler),
]

type ListEquipmentHandlerDependency = Annotated[
    ListEquipmentHandler,
    Depends(get_list_equipment_handler),
]
