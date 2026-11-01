"""Tests for validated AeroPulse settings."""

import pytest
from pydantic import ValidationError

from aeropulse.settings import Environment, Settings, load_settings


def base_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "postgresql+asyncpg://user:password@localhost:5432/aeropulse",
        "redis_url": "redis://localhost:6379/0",
    }
    values.update(overrides)
    return Settings.model_validate(values)


def test_settings_read_aeropulse_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEROPULSE_APP_NAME", "AeroPulse Test")
    monkeypatch.setenv("AEROPULSE_ENVIRONMENT", "test")
    monkeypatch.setenv("AEROPULSE_DEBUG", "true")
    monkeypatch.setenv(
        "AEROPULSE_DATABASE_URL",
        "postgresql+asyncpg://user:password@localhost:5432/aeropulse",
    )
    monkeypatch.setenv("AEROPULSE_REDIS_URL", "redis://localhost:6379/0")

    settings = load_settings()

    assert settings.app_name == "AeroPulse Test"
    assert settings.environment is Environment.TEST
    assert settings.debug is True


def test_settings_reject_debug_in_production() -> None:
    with pytest.raises(ValidationError, match="debug must be disabled in production"):
        base_settings(
            environment=Environment.PRODUCTION,
            debug=True,
        )


def test_settings_allow_production_when_debug_is_disabled() -> None:
    settings = base_settings(
        environment=Environment.PRODUCTION,
        debug=False,
    )

    assert settings.environment is Environment.PRODUCTION
    assert settings.debug is False


@pytest.mark.parametrize("timeout", [0, -1, 10.1])
def test_settings_reject_invalid_dependency_timeout(timeout: float) -> None:
    with pytest.raises(ValidationError):
        base_settings(dependency_timeout_seconds=timeout)


def test_secret_urls_are_redacted_in_settings_representation() -> None:
    settings = base_settings()

    representation = repr(settings)

    assert "password" not in representation
    assert "postgresql+asyncpg" not in representation
