"""Integration tests for AeroPulse operational HTTP endpoints."""

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.api.app import create_app
from aeropulse.settings import Environment, Settings


@dataclass
class FakeRuntimeResources:
    ready: bool = True
    closed: bool = False

    def create_database_session(self) -> AsyncSession:
        raise AssertionError("database session must not be requested by system endpoint tests")

    async def is_ready(self) -> bool:
        return self.ready

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def test_settings() -> Settings:
    return Settings.model_validate(
        {
            "app_name": "AeroPulse Test",
            "environment": Environment.TEST,
            "debug": False,
            "database_url": "postgresql+asyncpg://user:password@localhost:5432/aeropulse",
            "redis_url": "redis://localhost:6379/0",
        }
    )


def test_health_reports_liveness_without_application_lifespan(
    test_settings: Settings,
) -> None:
    app = create_app(test_settings)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["cache-control"] == "no-store"


def test_readiness_is_unavailable_before_lifespan_startup(
    test_settings: Settings,
) -> None:
    app = create_app(test_settings)
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert response.headers["cache-control"] == "no-store"


def test_readiness_is_available_when_dependencies_are_ready(
    test_settings: Settings,
) -> None:
    resources = FakeRuntimeResources(ready=True)
    app = create_app(test_settings, runtime_resources_factory=lambda _: resources)

    with TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert resources.closed is True


def test_readiness_becomes_unavailable_when_a_dependency_fails(
    test_settings: Settings,
) -> None:
    resources = FakeRuntimeResources(ready=True)
    app = create_app(test_settings, runtime_resources_factory=lambda _: resources)

    with TestClient(app) as client:
        initial_response = client.get("/ready")
        resources.ready = False
        degraded_response = client.get("/ready")

    assert initial_response.status_code == 200
    assert degraded_response.status_code == 503
    assert degraded_response.json() == {"status": "not_ready"}


def test_readiness_is_unavailable_after_shutdown(
    test_settings: Settings,
) -> None:
    resources = FakeRuntimeResources()
    app = create_app(test_settings, runtime_resources_factory=lambda _: resources)

    with TestClient(app):
        pass

    response_after_shutdown = TestClient(app).get("/ready")

    assert response_after_shutdown.status_code == 503


def test_operational_routes_are_excluded_from_openapi(
    test_settings: Settings,
) -> None:
    resources = FakeRuntimeResources()
    app = create_app(test_settings, runtime_resources_factory=lambda _: resources)

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    paths = response.json()["paths"]

    assert "/health" not in paths
    assert "/ready" not in paths


def test_application_uses_explicit_settings(
    test_settings: Settings,
) -> None:
    app = create_app(test_settings)

    assert app.title == "AeroPulse Test"
    assert app.debug is False
    assert app.state.settings is test_settings


def test_application_factory_can_load_environment_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEROPULSE_APP_NAME", "AeroPulse From Environment")
    monkeypatch.setenv("AEROPULSE_ENVIRONMENT", "test")
    monkeypatch.setenv("AEROPULSE_DEBUG", "false")
    monkeypatch.setenv(
        "AEROPULSE_DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5432/aeropulse",
    )
    monkeypatch.setenv("AEROPULSE_REDIS_URL", "redis://localhost:6379/0")

    app = create_app()

    assert app.title == "AeroPulse From Environment"


def test_api_documentation_surfaces_are_available(
    test_settings: Settings,
) -> None:
    resources = FakeRuntimeResources()
    app = create_app(test_settings, runtime_resources_factory=lambda _: resources)

    with TestClient(app) as client:
        swagger_response = client.get("/docs")
        redoc_response = client.get("/redoc")
        openapi_response = client.get("/openapi.json")

    assert swagger_response.status_code == 200
    assert "swagger-ui" in swagger_response.text.lower()

    assert redoc_response.status_code == 200
    assert "redoc" in redoc_response.text.lower()

    assert openapi_response.status_code == 200
    assert openapi_response.headers["content-type"].startswith("application/json")


def test_openapi_metadata_describes_aeropulse_and_orders_fleet_tags(
    test_settings: Settings,
) -> None:
    resources = FakeRuntimeResources()
    app = create_app(test_settings, runtime_resources_factory=lambda _: resources)

    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "AeroPulse Test"
    assert schema["info"]["summary"] == (
        "Aircraft predictive maintenance and fleet health engineering platform"
    )
    assert schema["info"]["license"] == {
        "name": "MIT",
        "identifier": "MIT",
    }
    assert [tag["name"] for tag in schema["tags"]] == [
        "aircraft",
        "equipment",
    ]
    assert "certified" in schema["info"]["description"].lower()
