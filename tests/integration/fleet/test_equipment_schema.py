"""Schema integration tests for the Equipment persistence model."""

import asyncio
import os
from typing import Any, TypedDict

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from aeropulse.settings import load_settings

pytestmark = [
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to test PostgreSQL schema",
    ),
]


class EquipmentConstraints(TypedDict):
    primary_key: str | None
    unique: set[str | None]
    checks: set[str | None]
    foreign_keys: set[str | None]
    indexes: set[str | None]
    columns: set[str]


def test_equipment_schema_has_required_integrity_constraints() -> None:
    async def scenario() -> None:
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        try:
            async with engine.connect() as connection:
                constraints = await connection.run_sync(_equipment_constraints)
        finally:
            await engine.dispose()

        assert constraints["primary_key"] == "pk_equipment"
        assert "uq_equipment_part_number_serial_number" in constraints["unique"]
        assert "ck_equipment_required_values" in constraints["checks"]
        assert "fk_equipment_aircraft_id_aircraft" in constraints["foreign_keys"]
        assert "ix_equipment_aircraft_created_at_id" in constraints["indexes"]
        assert constraints["columns"] >= {
            "id",
            "aircraft_id",
            "equipment_type",
            "part_number",
            "serial_number",
            "created_at",
        }

    asyncio.run(scenario())


def _equipment_constraints(connection: Any) -> EquipmentConstraints:
    inspector = inspect(connection)
    primary_key = inspector.get_pk_constraint("equipment")
    unique = inspector.get_unique_constraints("equipment")
    checks = inspector.get_check_constraints("equipment")
    foreign_keys = inspector.get_foreign_keys("equipment")
    indexes = inspector.get_indexes("equipment")
    columns = inspector.get_columns("equipment")
    return {
        "primary_key": primary_key["name"],
        "unique": {item["name"] for item in unique},
        "checks": {item["name"] for item in checks},
        "foreign_keys": {item["name"] for item in foreign_keys},
        "indexes": {item["name"] for item in indexes},
        "columns": {str(item["name"]) for item in columns},
    }
