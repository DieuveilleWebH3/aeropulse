"""Fleet aircraft HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from aeropulse.fleet.application.commands import (
    RegisterAircraftCommand,
    RetireAircraftCommand,
)
from aeropulse.fleet.application.queries import (
    DEFAULT_AIRCRAFT_PAGE_SIZE,
    MAX_AIRCRAFT_PAGE_SIZE,
    GetAircraftQuery,
    ListAircraftQuery,
)
from aeropulse.fleet.presentation.dependencies import (
    GetAircraftHandlerDependency,
    ListAircraftHandlerDependency,
    RegisterAircraftHandlerDependency,
    RetireAircraftHandlerDependency,
)
from aeropulse.fleet.presentation.schemas import (
    AircraftListResponse,
    AircraftResponse,
    ApiErrorResponse,
    RegisterAircraftRequest,
)

router = APIRouter(prefix="/api/v1", tags=["aircraft"])


@router.post(
    "/aircraft",
    response_model=AircraftResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": "Aircraft registration already exists.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ApiErrorResponse,
            "description": "Aircraft registration violates the Fleet domain policy.",
        },
    },
)
async def register_aircraft(
    payload: RegisterAircraftRequest,
    handler: RegisterAircraftHandlerDependency,
) -> AircraftResponse:
    """Register one aircraft in the Fleet."""
    aircraft = await handler.handle(RegisterAircraftCommand(registration=payload.registration))
    return AircraftResponse.from_domain(aircraft)


@router.get(
    "/aircraft",
    response_model=AircraftListResponse,
)
async def list_aircraft(
    handler: ListAircraftHandlerDependency,
    limit: Annotated[int, Query(ge=1, le=MAX_AIRCRAFT_PAGE_SIZE)] = DEFAULT_AIRCRAFT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AircraftListResponse:
    """Return one deterministic page of Fleet aircraft."""
    page = await handler.handle(
        ListAircraftQuery(
            limit=limit,
            offset=offset,
        )
    )
    return AircraftListResponse.from_application(page)


@router.get(
    "/aircraft/{aircraft_id}",
    response_model=AircraftResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Aircraft does not exist.",
        },
    },
)
async def get_aircraft(
    aircraft_id: UUID,
    handler: GetAircraftHandlerDependency,
) -> AircraftResponse:
    """Return one aircraft by stable identifier."""
    aircraft = await handler.handle(GetAircraftQuery(aircraft_id=aircraft_id))
    return AircraftResponse.from_domain(aircraft)


@router.post(
    "/aircraft/{aircraft_id}/retire",
    response_model=AircraftResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Aircraft does not exist.",
        },
    },
)
async def retire_aircraft(
    aircraft_id: UUID,
    handler: RetireAircraftHandlerDependency,
) -> AircraftResponse:
    """Retire one aircraft idempotently."""
    aircraft = await handler.handle(RetireAircraftCommand(aircraft_id=aircraft_id))
    return AircraftResponse.from_domain(aircraft)
