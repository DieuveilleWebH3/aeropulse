"""HTTP contract tests for retrieving and listing aircraft without external services."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.api.app import create_app
from aeropulse.fleet.application.errors import AircraftNotFound
from aeropulse.fleet.application.queries import (
    AircraftPage,
    GetAircraftQuery,
    ListAircraftQuery,
)
from aeropulse.fleet.domain.aircraft import Aircraft
from aeropulse.fleet.domain.value_objects import AircraftRegistration
from aeropulse.fleet.presentation.dependencies import (
    get_aircraft_handler,
    get_list_aircraft_handler,
)
from aeropulse.settings import Environment, Settings

AIRCRAFT_ID = UUID("77777777-7777-4777-8777-777777777777")
CREATED_AT = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)


@dataclass
class FakeRuntimeResources:
    closed: bool = False

    def create_database_session(self) -> AsyncSession:
        raise AssertionError("database session should be overridden by read handler dependencies")

    async def is_ready(self) -> bool:
        return True

    async def close(self) -> None:
        self.closed = True


class StubGetAircraftHandler:
    def __init__(self, result: Aircraft | None) -> None:
        self.result = result
        self.queries: list[GetAircraftQuery] = []

    async def handle(self, query: GetAircraftQuery) -> Aircraft:
        self.queries.append(query)
        if self.result is None:
            raise AircraftNotFound(query.aircraft_id)
        return self.result


class StubListAircraftHandler:
    def __init__(self, page: AircraftPage) -> None:
        self.page = page
        self.queries: list[ListAircraftQuery] = []

    async def handle(self, query: ListAircraftQuery) -> AircraftPage:
        self.queries.append(query)
        return self.page


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


def build_aircraft() -> Aircraft:
    return Aircraft(
        id=AIRCRAFT_ID,
        registration=AircraftRegistration("F-HABC"),
        created_at=CREATED_AT,
    )


def build_client(
    test_settings: Settings,
    *,
    get_handler: StubGetAircraftHandler,
    list_handler: StubListAircraftHandler,
) -> TestClient:
    resources = FakeRuntimeResources()
    app = create_app(test_settings, runtime_resources_factory=lambda _: resources)
    app.dependency_overrides[get_aircraft_handler] = lambda: get_handler
    app.dependency_overrides[get_list_aircraft_handler] = lambda: list_handler
    return TestClient(app)


def test_get_aircraft_returns_200_contract(test_settings: Settings) -> None:
    aircraft = build_aircraft()
    get_handler = StubGetAircraftHandler(aircraft)
    list_handler = StubListAircraftHandler(AircraftPage((), 0, 50, 0))

    with build_client(
        test_settings,
        get_handler=get_handler,
        list_handler=list_handler,
    ) as client:
        response = client.get(f"/api/v1/aircraft/{AIRCRAFT_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(AIRCRAFT_ID)
    assert response.json()["registration"] == "F-HABC"
    assert get_handler.queries == [GetAircraftQuery(aircraft_id=AIRCRAFT_ID)]


def test_get_aircraft_returns_stable_404_contract(test_settings: Settings) -> None:
    get_handler = StubGetAircraftHandler(None)
    list_handler = StubListAircraftHandler(AircraftPage((), 0, 50, 0))

    with build_client(
        test_settings,
        get_handler=get_handler,
        list_handler=list_handler,
    ) as client:
        response = client.get(f"/api/v1/aircraft/{AIRCRAFT_ID}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "aircraft_not_found",
            "message": f"aircraft not found: {AIRCRAFT_ID}",
            "field": None,
        }
    }


def test_list_aircraft_returns_page_contract(test_settings: Settings) -> None:
    aircraft = build_aircraft()
    get_handler = StubGetAircraftHandler(aircraft)
    list_handler = StubListAircraftHandler(
        AircraftPage(
            items=(aircraft,),
            total=17,
            limit=10,
            offset=5,
        )
    )

    with build_client(
        test_settings,
        get_handler=get_handler,
        list_handler=list_handler,
    ) as client:
        response = client.get("/api/v1/aircraft?limit=10&offset=5")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": str(AIRCRAFT_ID),
                "registration": "F-HABC",
                "status": "active",
                "created_at": "2026-11-01T10:00:00Z",
                "retired_at": None,
            }
        ],
        "total": 17,
        "limit": 10,
        "offset": 5,
    }
    assert list_handler.queries == [ListAircraftQuery(limit=10, offset=5)]


@pytest.mark.parametrize(
    "query_string",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
    ],
)
def test_list_aircraft_rejects_invalid_pagination(
    test_settings: Settings,
    query_string: str,
) -> None:
    aircraft = build_aircraft()
    get_handler = StubGetAircraftHandler(aircraft)
    list_handler = StubListAircraftHandler(AircraftPage((aircraft,), 1, 50, 0))

    with build_client(
        test_settings,
        get_handler=get_handler,
        list_handler=list_handler,
    ) as client:
        response = client.get(f"/api/v1/aircraft?{query_string}")

    assert response.status_code == 422
    assert list_handler.queries == []
