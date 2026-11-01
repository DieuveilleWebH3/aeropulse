"""Fleet aircraft HTTP routes."""

from fastapi import APIRouter, status

from aeropulse.fleet.application.commands import RegisterAircraftCommand
from aeropulse.fleet.presentation.dependencies import (
    RegisterAircraftHandlerDependency,
)
from aeropulse.fleet.presentation.schemas import (
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
