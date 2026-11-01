"""Live API-to-PostgreSQL integration tests for aircraft retirement."""

import asyncio
import os
from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import create_async_engine

from aeropulse.api.app import create_app
from aeropulse.fleet.infrastructure.persistence.schema import aircraft_table
from aeropulse.settings import load_settings

pytestmark = [
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to test live aircraft API",
    ),
]


def unique_registration() -> str:
    return f"X-{uuid4().hex[:8].upper()}"


async def load_row(aircraft_id: UUID) -> Mapping[str, Any] | None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                select(aircraft_table).where(aircraft_table.c.id == aircraft_id)
            )
            row = result.mappings().one_or_none()
            return None if row is None else dict(row)
    finally:
        await engine.dispose()


async def cleanup(aircraft_id: UUID) -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            await connection.execute(
                delete(aircraft_table).where(aircraft_table.c.id == aircraft_id)
            )
    finally:
        await engine.dispose()


def test_registered_aircraft_can_be_retired_idempotently() -> None:
    registration = unique_registration()
    aircraft_id: UUID | None = None

    try:
        with TestClient(create_app()) as client:
            created = client.post(
                "/api/v1/aircraft",
                json={"registration": registration},
            )
            assert created.status_code == 201
            aircraft_id = UUID(created.json()["id"])
            assert created.json()["retired_at"] is None

            first = client.post(f"/api/v1/aircraft/{aircraft_id}/retire")
            second = client.post(f"/api/v1/aircraft/{aircraft_id}/retire")
            retrieved = client.get(f"/api/v1/aircraft/{aircraft_id}")

        assert first.status_code == 200
        assert second.status_code == 200
        assert retrieved.status_code == 200

        first_body = first.json()
        second_body = second.json()
        retrieved_body = retrieved.json()

        assert first_body["status"] == "retired"
        assert first_body["retired_at"] is not None
        assert second_body["retired_at"] == first_body["retired_at"]
        assert retrieved_body["retired_at"] == first_body["retired_at"]

        persisted = asyncio.run(load_row(aircraft_id))
        assert persisted is not None
        assert persisted["status"] == "retired"
        assert persisted["retired_at"] is not None
    finally:
        if aircraft_id is not None:
            asyncio.run(cleanup(aircraft_id))


def test_retire_unknown_aircraft_returns_404() -> None:
    unknown_id = uuid4()

    with TestClient(create_app()) as client:
        response = client.post(f"/api/v1/aircraft/{unknown_id}/retire")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "aircraft_not_found"
