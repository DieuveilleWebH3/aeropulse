"""HTTP error translation for Fleet business failures."""

from typing import cast

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from aeropulse.fleet.application.errors import (
    AircraftNotFound,
    AircraftRegistrationAlreadyExists,
    AircraftRetiredForEquipmentRegistration,
    EquipmentAlreadyExists,
    EquipmentNotFound,
)
from aeropulse.fleet.domain.errors import (
    InvalidAircraftRegistration,
    InvalidEquipmentPartNumber,
    InvalidEquipmentSerialNumber,
    InvalidEquipmentType,
)
from aeropulse.fleet.presentation.schemas import ApiErrorDetail, ApiErrorResponse


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    field: str | None,
) -> JSONResponse:
    payload = ApiErrorResponse(
        error=ApiErrorDetail(
            code=code,
            message=message,
            field=field,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


async def handle_invalid_aircraft_registration(
    request: Request,
    exc: Exception,
) -> Response:
    """Map a Fleet registration invariant violation to HTTP 422."""
    del request
    error = cast(InvalidAircraftRegistration, exc)
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="invalid_aircraft_registration",
        message=str(error),
        field="registration",
    )


async def handle_aircraft_registration_already_exists(
    request: Request,
    exc: Exception,
) -> Response:
    """Map duplicate aircraft registration to HTTP 409."""
    del request
    error = cast(AircraftRegistrationAlreadyExists, exc)
    return _error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="aircraft_registration_already_exists",
        message=str(error),
        field="registration",
    )


async def handle_aircraft_not_found(
    request: Request,
    exc: Exception,
) -> Response:
    """Map a missing aircraft to HTTP 404."""
    del request
    error = cast(AircraftNotFound, exc)
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="aircraft_not_found",
        message=str(error),
        field=None,
    )


async def handle_equipment_not_found(
    request: Request,
    exc: Exception,
) -> Response:
    """Map missing equipment to HTTP 404."""
    del request
    error = cast(EquipmentNotFound, exc)
    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="equipment_not_found",
        message=str(error),
        field=None,
    )


async def handle_equipment_already_exists(
    request: Request,
    exc: Exception,
) -> Response:
    """Map duplicate physical equipment identity to HTTP 409."""
    del request
    error = cast(EquipmentAlreadyExists, exc)
    return _error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="equipment_already_exists",
        message=str(error),
        field=None,
    )


async def handle_retired_aircraft_equipment_registration(
    request: Request,
    exc: Exception,
) -> Response:
    """Map equipment registration against a retired aircraft to HTTP 409."""
    del request
    error = cast(AircraftRetiredForEquipmentRegistration, exc)
    return _error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="aircraft_retired_for_equipment_registration",
        message=str(error),
        field=None,
    )


async def handle_invalid_equipment_type(
    request: Request,
    exc: Exception,
) -> Response:
    """Map equipment-type domain validation to HTTP 422."""
    del request
    error = cast(InvalidEquipmentType, exc)
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="invalid_equipment_type",
        message=str(error),
        field="equipment_type",
    )


async def handle_invalid_equipment_part_number(
    request: Request,
    exc: Exception,
) -> Response:
    """Map part-number domain validation to HTTP 422."""
    del request
    error = cast(InvalidEquipmentPartNumber, exc)
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="invalid_equipment_part_number",
        message=str(error),
        field="part_number",
    )


async def handle_invalid_equipment_serial_number(
    request: Request,
    exc: Exception,
) -> Response:
    """Map serial-number domain validation to HTTP 422."""
    del request
    error = cast(InvalidEquipmentSerialNumber, exc)
    return _error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="invalid_equipment_serial_number",
        message=str(error),
        field="serial_number",
    )


def register_fleet_exception_handlers(app: FastAPI) -> None:
    """Register Fleet business-to-HTTP exception mappings."""
    app.add_exception_handler(
        InvalidAircraftRegistration,
        handle_invalid_aircraft_registration,
    )
    app.add_exception_handler(
        AircraftRegistrationAlreadyExists,
        handle_aircraft_registration_already_exists,
    )
    app.add_exception_handler(
        AircraftNotFound,
        handle_aircraft_not_found,
    )
    app.add_exception_handler(
        EquipmentNotFound,
        handle_equipment_not_found,
    )
    app.add_exception_handler(
        EquipmentAlreadyExists,
        handle_equipment_already_exists,
    )
    app.add_exception_handler(
        AircraftRetiredForEquipmentRegistration,
        handle_retired_aircraft_equipment_registration,
    )
    app.add_exception_handler(
        InvalidEquipmentType,
        handle_invalid_equipment_type,
    )
    app.add_exception_handler(
        InvalidEquipmentPartNumber,
        handle_invalid_equipment_part_number,
    )
    app.add_exception_handler(
        InvalidEquipmentSerialNumber,
        handle_invalid_equipment_serial_number,
    )
