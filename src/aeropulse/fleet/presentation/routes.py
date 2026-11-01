"""Fleet HTTP routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from aeropulse.fleet.application.commands import (
    RegisterAircraftCommand,
    RegisterEquipmentCommand,
    RetireAircraftCommand,
)
from aeropulse.fleet.application.queries import (
    DEFAULT_AIRCRAFT_PAGE_SIZE,
    DEFAULT_EQUIPMENT_PAGE_SIZE,
    MAX_AIRCRAFT_PAGE_SIZE,
    MAX_EQUIPMENT_PAGE_SIZE,
    GetAircraftQuery,
    GetEquipmentQuery,
    ListAircraftQuery,
    ListEquipmentQuery,
)
from aeropulse.fleet.presentation.dependencies import (
    GetAircraftHandlerDependency,
    GetEquipmentHandlerDependency,
    ListAircraftHandlerDependency,
    ListEquipmentHandlerDependency,
    RegisterAircraftHandlerDependency,
    RegisterEquipmentHandlerDependency,
    RetireAircraftHandlerDependency,
)
from aeropulse.fleet.presentation.schemas import (
    AircraftListResponse,
    AircraftResponse,
    ApiErrorResponse,
    EquipmentListResponse,
    EquipmentResponse,
    RegisterAircraftRequest,
    RegisterEquipmentRequest,
)

router = APIRouter(prefix="/api/v1")


@router.post(
    "/aircraft",
    response_model=AircraftResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["aircraft"],
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
    tags=["aircraft"],
)
async def list_aircraft(
    handler: ListAircraftHandlerDependency,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_AIRCRAFT_PAGE_SIZE),
    ] = DEFAULT_AIRCRAFT_PAGE_SIZE,
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
    tags=["aircraft"],
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
    tags=["aircraft"],
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


@router.post(
    "/aircraft/{aircraft_id}/equipment",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["equipment"],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Parent aircraft does not exist.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": ("Equipment identity already exists or the aircraft is retired."),
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ApiErrorResponse,
            "description": "Equipment identity violates the Fleet domain policy.",
        },
    },
)
async def register_equipment(
    aircraft_id: UUID,
    payload: RegisterEquipmentRequest,
    handler: RegisterEquipmentHandlerDependency,
) -> EquipmentResponse:
    """Register maintainable equipment against one active aircraft."""
    equipment = await handler.handle(
        RegisterEquipmentCommand(
            aircraft_id=aircraft_id,
            equipment_type=payload.equipment_type,
            part_number=payload.part_number,
            serial_number=payload.serial_number,
        )
    )
    return EquipmentResponse.from_domain(equipment)


@router.get(
    "/equipment/{equipment_id}",
    response_model=EquipmentResponse,
    tags=["equipment"],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Equipment does not exist.",
        },
    },
)
async def get_equipment(
    equipment_id: UUID,
    handler: GetEquipmentHandlerDependency,
) -> EquipmentResponse:
    """Return one equipment item by stable identifier."""
    equipment = await handler.handle(GetEquipmentQuery(equipment_id=equipment_id))
    return EquipmentResponse.from_domain(equipment)


@router.get(
    "/aircraft/{aircraft_id}/equipment",
    response_model=EquipmentListResponse,
    tags=["equipment"],
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "Parent aircraft does not exist.",
        },
    },
)
async def list_equipment(
    aircraft_id: UUID,
    handler: ListEquipmentHandlerDependency,
    limit: Annotated[
        int,
        Query(ge=1, le=MAX_EQUIPMENT_PAGE_SIZE),
    ] = DEFAULT_EQUIPMENT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EquipmentListResponse:
    """Return one deterministic equipment page for an aircraft."""
    page = await handler.handle(
        ListEquipmentQuery(
            aircraft_id=aircraft_id,
            limit=limit,
            offset=offset,
        )
    )
    return EquipmentListResponse.from_application(page)
