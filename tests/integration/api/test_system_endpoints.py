"""Integration tests for AeroPulse operational HTTP endpoints."""

import pytest
from fastapi.testclient import TestClient

from aeropulse.api.app import create_app
from aeropulse.settings import Environment, Settings


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        app_name="AeroPulse Test",
        environment=Environment.TEST,
        debug=False,
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


def test_readiness_is_available_during_lifespan_and_unavailable_after_shutdown(
    test_settings: Settings,
) -> None:
    app = create_app(test_settings)

    with TestClient(app) as client:
        response = client.get("/ready")

        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

    client_after_shutdown = TestClient(app)
    response_after_shutdown = client_after_shutdown.get("/ready")

    assert response_after_shutdown.status_code == 503
    assert response_after_shutdown.json() == {"status": "not_ready"}


def test_operational_routes_are_excluded_from_openapi(
    test_settings: Settings,
) -> None:
    app = create_app(test_settings)

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

    app = create_app()

    assert app.title == "AeroPulse From Environment"
