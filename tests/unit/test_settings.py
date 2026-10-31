"""Tests for validated AeroPulse settings."""

import pytest
from pydantic import ValidationError

from aeropulse.settings import Environment, Settings


def test_settings_read_aeropulse_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEROPULSE_APP_NAME", "AeroPulse Test")
    monkeypatch.setenv("AEROPULSE_ENVIRONMENT", "test")
    monkeypatch.setenv("AEROPULSE_DEBUG", "true")

    settings = Settings()

    assert settings.app_name == "AeroPulse Test"
    assert settings.environment is Environment.TEST
    assert settings.debug is True


def test_settings_reject_debug_in_production() -> None:
    with pytest.raises(ValidationError, match="debug must be disabled in production"):
        Settings(
            environment=Environment.PRODUCTION,
            debug=True,
        )


def test_settings_allow_production_when_debug_is_disabled() -> None:
    settings = Settings(
        environment=Environment.PRODUCTION,
        debug=False,
    )

    assert settings.environment is Environment.PRODUCTION
    assert settings.debug is False
