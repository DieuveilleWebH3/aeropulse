"""HTTP contract tests for aircraft retirement without external services."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.api.app import create_app
from aeropulse.fleet.application.commands import RetireAircraftCommand
from aeropulse.fleet.application.errors import AircraftNotFound
from aeropulse.fleet.domain.aircraft import Aircraft, AircraftStatus
from aeropulse.fleet.domain.value_objects import AircraftRegistration
from aeropulse.fleet.presentation.dependencies import get_retire_aircraft_handler
from aeropulse.settings import Environment, Settings

AIRCRAFT_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
CREATED_AT = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)
RETIRED_AT = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


@dataclass
class FakeRuntimeResources:
    def create_database_session(self) -> AsyncSession:
        raise AssertionError("database session should be overridden")

    async def is_ready(self) -> bool:
        return True

    async def close(self) -> None:
        return None


class StubRetireAircraftHandler:
    def __init__(
        self,
        *,
        result: Aircraft | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.commands: list[RetireAircraftCommand] = []

    async def handle(self, command: RetireAircraftCommand) -> Aircraft:
        self.commands.append(command)
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise AssertionError("stub retirement handler has no result")
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
    settings: Settings,
    handler: StubRetireAircraftHandler,
) -> TestClient:
    app = create_app(
        settings,
        runtime_resources_factory=lambda _: FakeRuntimeResources(),
    )
    app.dependency_overrides[get_retire_aircraft_handler] = lambda: handler
    return TestClient(app)


def test_retire_aircraft_returns_200_retired_contract(
    test_settings: Settings,
) -> None:
    aircraft = Aircraft.rehydrate(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        status=AircraftStatus.RETIRED,
        created_at=CREATED_AT,
        retired_at=RETIRED_AT,
    )
    handler = StubRetireAircraftHandler(result=aircraft)

    with build_client(test_settings, handler) as client:
        response = client.post(f"/api/v1/aircraft/{AIRCRAFT_ID}/retire")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(AIRCRAFT_ID),
        "registration": "F-HABC",
        "status": "retired",
        "created_at": "2026-11-01T10:00:00Z",
        "retired_at": "2026-11-01T12:00:00Z",
    }
    assert handler.commands == [RetireAircraftCommand(AIRCRAFT_ID)]


def test_retire_unknown_aircraft_returns_404(test_settings: Settings) -> None:
    handler = StubRetireAircraftHandler(error=AircraftNotFound(AIRCRAFT_ID))

    with build_client(test_settings, handler) as client:
        response = client.post(f"/api/v1/aircraft/{AIRCRAFT_ID}/retire")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "aircraft_not_found"


def test_retirement_is_documented_in_openapi(test_settings: Settings) -> None:
    aircraft = Aircraft.rehydrate(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        status=AircraftStatus.RETIRED,
        created_at=CREATED_AT,
        retired_at=RETIRED_AT,
    )
    handler = StubRetireAircraftHandler(result=aircraft)

    with build_client(test_settings, handler) as client:
        operation = client.get("/openapi.json").json()["paths"][
            "/api/v1/aircraft/{aircraft_id}/retire"
        ]["post"]

    assert operation["responses"].keys() >= {"200", "404", "422"}
