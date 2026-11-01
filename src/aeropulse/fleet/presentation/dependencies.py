"""FastAPI dependency composition for Fleet use cases."""

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.api.runtime import RuntimeResources
from aeropulse.fleet.application.get_aircraft import GetAircraftHandler
from aeropulse.fleet.application.list_aircraft import ListAircraftHandler
from aeropulse.fleet.application.register_aircraft import RegisterAircraftHandler
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
