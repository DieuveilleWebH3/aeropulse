"""Live API-to-PostgreSQL integration tests for Fleet aircraft reads."""

import asyncio
import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
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
    return f"Q-{uuid4().hex[:8].upper()}"


async def current_aircraft_count() -> int:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            result = await connection.execute(select(func.count()).select_from(aircraft_table))
            return int(result.scalar_one())
    finally:
        await engine.dispose()


async def delete_aircraft(aircraft_id: UUID) -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            await connection.execute(
                delete(aircraft_table).where(aircraft_table.c.id == aircraft_id)
            )
    finally:
        await engine.dispose()


def test_registered_aircraft_can_be_retrieved_and_listed() -> None:
    registration = unique_registration()
    before_count = asyncio.run(current_aircraft_count())
    aircraft_id: UUID | None = None

    try:
        with TestClient(create_app()) as client:
            created = client.post(
                "/api/v1/aircraft",
                json={"registration": registration},
            )
            assert created.status_code == 201
            aircraft_id = UUID(created.json()["id"])

            retrieved = client.get(f"/api/v1/aircraft/{aircraft_id}")
            page = client.get(
                "/api/v1/aircraft",
                params={"limit": 10, "offset": before_count},
            )

        assert retrieved.status_code == 200
        assert retrieved.json()["id"] == str(aircraft_id)
        assert retrieved.json()["registration"] == registration

        assert page.status_code == 200
        assert page.json()["total"] >= before_count + 1
        assert any(item["id"] == str(aircraft_id) for item in page.json()["items"])
    finally:
        if aircraft_id is not None:
            asyncio.run(delete_aircraft(aircraft_id))


def test_unknown_aircraft_returns_404() -> None:
    unknown_id = uuid4()

    with TestClient(create_app()) as client:
        response = client.get(f"/api/v1/aircraft/{unknown_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "aircraft_not_found"
