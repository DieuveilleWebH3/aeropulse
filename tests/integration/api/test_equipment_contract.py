"""HTTP contract tests for Equipment endpoints without external services."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.api.app import create_app
from aeropulse.fleet.application.commands import RegisterEquipmentCommand
from aeropulse.fleet.application.errors import (
    AircraftNotFound,
    AircraftRetiredForEquipmentRegistration,
    EquipmentAlreadyExists,
    EquipmentNotFound,
)
from aeropulse.fleet.application.queries import (
    EquipmentPage,
    GetEquipmentQuery,
    ListEquipmentQuery,
)
from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.errors import InvalidEquipmentType
from aeropulse.fleet.domain.value_objects import (
    EquipmentPartNumber,
    EquipmentSerialNumber,
    EquipmentType,
)
from aeropulse.fleet.presentation.dependencies import (
    get_equipment_handler,
    get_list_equipment_handler,
    get_register_equipment_handler,
)
from aeropulse.settings import Environment, Settings

AIRCRAFT_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")
EQUIPMENT_ID = UUID("11111111-2222-4333-8444-555555555555")
CREATED_AT = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)


def equipment() -> Equipment:
    return Equipment(
        id=EQUIPMENT_ID,
        aircraft_id=AIRCRAFT_ID,
        equipment_type=EquipmentType("ENGINE-CONTROL"),
        part_number=EquipmentPartNumber("PN-ab/01"),
        serial_number=EquipmentSerialNumber("Sn-00a"),
        created_at=CREATED_AT,
    )


@dataclass
class FakeRuntimeResources:
    def create_database_session(self) -> AsyncSession:
        raise AssertionError("database session should be overridden")

    async def is_ready(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class StubHandler:
    def __init__(self, *, result: object | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[object] = []

    async def handle(self, command: object) -> object:
        self.calls.append(command)
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise AssertionError("stub handler has no result")
        return self.result


@pytest.fixture
def settings() -> Settings:
    return Settings.model_validate(
        {
            "app_name": "AeroPulse Test",
            "environment": Environment.TEST,
            "debug": False,
            "database_url": "postgresql+asyncpg://unused@127.0.0.1:5432/aeropulse",
            "redis_url": "redis://127.0.0.1:6379/0",
        }
    )


def client_with_override(
    settings: Settings,
    dependency: Callable[..., Any],
    handler: StubHandler,
) -> TestClient:
    app = create_app(
        settings,
        runtime_resources_factory=lambda _: FakeRuntimeResources(),
    )
    app.dependency_overrides[dependency] = lambda: handler
    return TestClient(app)


def test_register_equipment_returns_201_contract(settings: Settings) -> None:
    handler = StubHandler(result=equipment())

    with client_with_override(
        settings,
        get_register_equipment_handler,
        handler,
    ) as client:
        response = client.post(
            f"/api/v1/aircraft/{AIRCRAFT_ID}/equipment",
            json={
                "equipment_type": " engine-control ",
                "part_number": " PN-ab/01 ",
                "serial_number": " Sn-00a ",
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(EQUIPMENT_ID),
        "aircraft_id": str(AIRCRAFT_ID),
        "equipment_type": "ENGINE-CONTROL",
        "part_number": "PN-ab/01",
        "serial_number": "Sn-00a",
        "created_at": "2026-11-01T10:00:00Z",
    }
    assert handler.calls == [
        RegisterEquipmentCommand(
            aircraft_id=AIRCRAFT_ID,
            equipment_type=" engine-control ",
            part_number=" PN-ab/01 ",
            serial_number=" Sn-00a ",
        )
    ]


@pytest.mark.parametrize(
    ("error", "status_code", "code"),
    [
        (
            AircraftNotFound(AIRCRAFT_ID),
            404,
            "aircraft_not_found",
        ),
        (
            AircraftRetiredForEquipmentRegistration(AIRCRAFT_ID),
            409,
            "aircraft_retired_for_equipment_registration",
        ),
        (
            EquipmentAlreadyExists(
                EquipmentPartNumber("PN-ab/01"),
                EquipmentSerialNumber("Sn-00a"),
            ),
            409,
            "equipment_already_exists",
        ),
        (
            InvalidEquipmentType("equipment type contains unsupported characters"),
            422,
            "invalid_equipment_type",
        ),
    ],
)
def test_register_equipment_maps_business_errors(
    settings: Settings,
    error: Exception,
    status_code: int,
    code: str,
) -> None:
    handler = StubHandler(error=error)

    with client_with_override(
        settings,
        get_register_equipment_handler,
        handler,
    ) as client:
        response = client.post(
            f"/api/v1/aircraft/{AIRCRAFT_ID}/equipment",
            json={
                "equipment_type": "ENGINE-CONTROL",
                "part_number": "PN-ab/01",
                "serial_number": "Sn-00a",
            },
        )

    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


def test_get_equipment_returns_200_contract(settings: Settings) -> None:
    handler = StubHandler(result=equipment())

    with client_with_override(
        settings,
        get_equipment_handler,
        handler,
    ) as client:
        response = client.get(f"/api/v1/equipment/{EQUIPMENT_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(EQUIPMENT_ID)
    assert handler.calls == [GetEquipmentQuery(EQUIPMENT_ID)]


def test_get_equipment_returns_404(settings: Settings) -> None:
    handler = StubHandler(error=EquipmentNotFound(EQUIPMENT_ID))

    with client_with_override(
        settings,
        get_equipment_handler,
        handler,
    ) as client:
        response = client.get(f"/api/v1/equipment/{EQUIPMENT_ID}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "equipment_not_found"


def test_list_equipment_returns_paginated_contract(settings: Settings) -> None:
    handler = StubHandler(
        result=EquipmentPage(
            items=(equipment(),),
            total=1,
            limit=25,
            offset=5,
        )
    )

    with client_with_override(
        settings,
        get_list_equipment_handler,
        handler,
    ) as client:
        response = client.get(f"/api/v1/aircraft/{AIRCRAFT_ID}/equipment?limit=25&offset=5")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": str(EQUIPMENT_ID),
                "aircraft_id": str(AIRCRAFT_ID),
                "equipment_type": "ENGINE-CONTROL",
                "part_number": "PN-ab/01",
                "serial_number": "Sn-00a",
                "created_at": "2026-11-01T10:00:00Z",
            }
        ],
        "total": 1,
        "limit": 25,
        "offset": 5,
    }
    assert handler.calls == [
        ListEquipmentQuery(
            aircraft_id=AIRCRAFT_ID,
            limit=25,
            offset=5,
        )
    ]


def test_list_equipment_rejects_invalid_pagination_before_handler(
    settings: Settings,
) -> None:
    handler = StubHandler(result=EquipmentPage(items=(), total=0, limit=50, offset=0))

    with client_with_override(
        settings,
        get_list_equipment_handler,
        handler,
    ) as client:
        response = client.get(f"/api/v1/aircraft/{AIRCRAFT_ID}/equipment?limit=101")

    assert response.status_code == 422
    assert handler.calls == []


def test_equipment_endpoints_are_documented_in_openapi(settings: Settings) -> None:
    handler = StubHandler(result=equipment())
    app = create_app(
        settings,
        runtime_resources_factory=lambda _: FakeRuntimeResources(),
    )
    app.dependency_overrides[get_equipment_handler] = lambda: handler

    with TestClient(app) as client:
        paths = client.get("/openapi.json").json()["paths"]

    assert "/api/v1/aircraft/{aircraft_id}/equipment" in paths
    assert "/api/v1/equipment/{equipment_id}" in paths
