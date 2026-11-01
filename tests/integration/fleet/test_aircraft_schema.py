"""Integration tests for the migrated Fleet aircraft database schema."""

import asyncio
import os
from typing import TypedDict

import pytest
from sqlalchemy import Connection, inspect
from sqlalchemy.ext.asyncio import create_async_engine

from aeropulse.settings import load_settings


class AircraftConstraints(TypedDict):
    primary_key: str | None
    unique: set[str | None]
    checks: set[str | None]


pytestmark = [
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to inspect live PostgreSQL schema",
    ),
]


def test_aircraft_schema_has_required_integrity_constraints() -> None:
    async def scenario() -> None:
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())

        try:
            async with engine.connect() as connection:
                constraints = await connection.run_sync(_aircraft_constraints)
        finally:
            await engine.dispose()

        assert constraints["primary_key"] == "pk_aircraft"
        assert "uq_aircraft_registration" in constraints["unique"]
        assert "ck_aircraft_status" in constraints["checks"]

    asyncio.run(scenario())


def _aircraft_constraints(connection: Connection) -> AircraftConstraints:
    inspector = inspect(connection)
    primary_key = inspector.get_pk_constraint("aircraft")
    unique_constraints = inspector.get_unique_constraints("aircraft")
    check_constraints = inspector.get_check_constraints("aircraft")

    return {
        "primary_key": primary_key["name"],
        "unique": {item["name"] for item in unique_constraints},
        "checks": {item["name"] for item in check_constraints},
    }
