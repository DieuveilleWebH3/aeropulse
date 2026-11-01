"""HTTP contract tests for aircraft registration without external services."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.api.app import create_app
from aeropulse.fleet.application.commands import RegisterAircraftCommand
from aeropulse.fleet.application.errors import AircraftRegistrationAlreadyExists
from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.errors import InvalidAircraftRegistration
from aeropulse.fleet.domain.value_objects import AircraftRegistration
from aeropulse.fleet.presentation.dependencies import get_register_aircraft_handler
from aeropulse.settings import Environment, Settings

AIRCRAFT_ID = UUID("33333333-3333-4333-8333-333333333333")
CREATED_AT = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)


@dataclass
class FakeRuntimeResources:
    closed: bool = False

    def create_database_session(self) -> AsyncSession:
        raise AssertionError("database session should be overridden by the handler dependency")

    async def is_ready(self) -> bool:
        return True

    async def close(self) -> None:
        self.closed = True


class StubRegisterAircraftHandler:
    def __init__(
        self,
        *,
        result: Aircraft | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.commands: list[RegisterAircraftCommand] = []

    async def handle(self, command: RegisterAircraftCommand) -> Aircraft:
        self.commands.append(command)
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise AssertionError("stub handler has no configured result")
        return self.result


@pytest.fixture
def test_settings() -> Settings:
    return Settings.model_validate(
        {
            "app_name": "AeroPulse Test",
            "environment": Environment.TEST,
            "debug": False,
            "database_url": "postgresql+asyncpg://unused@127.0.0.1:5432/aeropulse",
            "redis_url": "redis://127.0.0.1:6379/0",
        }
    )


def build_client(
    test_settings: Settings,
    handler: StubRegisterAircraftHandler,
) -> tuple[TestClient, FakeRuntimeResources]:
    resources = FakeRuntimeResources()
    app = create_app(
        test_settings,
        runtime_resources_factory=lambda _: resources,
    )
    app.dependency_overrides[get_register_aircraft_handler] = lambda: handler
    return TestClient(app), resources


def test_register_aircraft_returns_201_contract(test_settings: Settings) -> None:
    aircraft = Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=CREATED_AT,
    )
    handler = StubRegisterAircraftHandler(result=aircraft)
    client, resources = build_client(test_settings, handler)

    with client:
        response = client.post(
            "/api/v1/aircraft",
            json={"registration": " f-habc "},
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(AIRCRAFT_ID),
        "registration": "F-HABC",
        "status": "active",
        "created_at": "2026-11-01T10:00:00Z",
        "retired_at": None,
    }
    assert handler.commands == [RegisterAircraftCommand(registration=" f-habc ")]
    assert resources.closed is True


def test_duplicate_registration_returns_stable_409_error(
    test_settings: Settings,
) -> None:
    handler = StubRegisterAircraftHandler(
        error=AircraftRegistrationAlreadyExists(AircraftRegistration("F-HABC"))
    )
    client, _ = build_client(test_settings, handler)

    with client:
        response = client.post(
            "/api/v1/aircraft",
            json={"registration": "F-HABC"},
        )

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "aircraft_registration_already_exists",
            "message": "aircraft registration already exists: F-HABC",
            "field": "registration",
        }
    }


def test_invalid_registration_returns_stable_422_error(
    test_settings: Settings,
) -> None:
    handler = StubRegisterAircraftHandler(
        error=InvalidAircraftRegistration("aircraft registration contains invalid characters")
    )
    client, _ = build_client(test_settings, handler)

    with client:
        response = client.post(
            "/api/v1/aircraft",
            json={"registration": "F/HABC"},
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "invalid_aircraft_registration",
            "message": "aircraft registration contains invalid characters",
            "field": "registration",
        }
    }


def test_request_rejects_unknown_fields(test_settings: Settings) -> None:
    handler = StubRegisterAircraftHandler(
        result=Aircraft(
            id=AIRCRAFT_ID,
            registration=AircraftRegistration("F-HABC"),
            created_at=CREATED_AT,
        )
    )
    client, _ = build_client(test_settings, handler)

    with client:
        response = client.post(
            "/api/v1/aircraft",
            json={"registration": "F-HABC", "unexpected": True},
        )

    assert response.status_code == 422
    assert handler.commands == []


def test_aircraft_registration_is_documented_in_openapi(
    test_settings: Settings,
) -> None:
    handler = StubRegisterAircraftHandler(
        result=Aircraft(
            id=AIRCRAFT_ID,
            registration=AircraftRegistration("F-HABC"),
            created_at=CREATED_AT,
        )
    )
    client, _ = build_client(test_settings, handler)

    with client:
        response = client.get("/openapi.json")

    operation = response.json()["paths"]["/api/v1/aircraft"]["post"]

    assert operation["responses"].keys() >= {"201", "409", "422"}
