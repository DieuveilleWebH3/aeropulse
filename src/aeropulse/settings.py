"""Validated runtime configuration for AeroPulse."""

from enum import StrEnum
from typing import Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported AeroPulse runtime environments."""

    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and an optional local .env file."""

    model_config = SettingsConfigDict(
        env_prefix="AEROPULSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AeroPulse"
    environment: Environment = Environment.LOCAL
    debug: bool = False

    database_url: SecretStr
    redis_url: SecretStr
    dependency_timeout_seconds: float = Field(default=1.0, gt=0.0, le=10.0)

    @model_validator(mode="after")
    def reject_debug_in_production(self) -> Self:
        """Prevent accidental debug mode in production."""
        if self.environment is Environment.PRODUCTION and self.debug:
            raise ValueError("debug must be disabled in production")
        return self


def load_settings() -> Settings:
    """Load and validate settings from configured settings sources."""
    return Settings.model_validate({})
