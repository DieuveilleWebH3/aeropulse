"""Live API-to-PostgreSQL integration tests for Equipment endpoints."""

import asyncio
import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine

from aeropulse.api.app import create_app
from aeropulse.fleet.infrastructure.persistence.schema import (
    aircraft_table,
    equipment_table,
)
from aeropulse.settings import load_settings

pytestmark = [
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to test live equipment API",
    ),
]


async def cleanup(aircraft_ids: set[UUID]) -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            if aircraft_ids:
                await connection.execute(
                    delete(equipment_table).where(equipment_table.c.aircraft_id.in_(aircraft_ids))
                )
                await connection.execute(
                    delete(aircraft_table).where(aircraft_table.c.id.in_(aircraft_ids))
                )
    finally:
        await engine.dispose()


def registration(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:6].upper()}"


def test_equipment_full_http_flow_and_duplicate_conflict() -> None:
    aircraft_ids: set[UUID] = set()

    try:
        with TestClient(create_app()) as client:
            aircraft_response = client.post(
                "/api/v1/aircraft",
                json={"registration": registration("EQ")},
            )
            assert aircraft_response.status_code == 201
            aircraft_id = UUID(aircraft_response.json()["id"])
            aircraft_ids.add(aircraft_id)

            create_response = client.post(
                f"/api/v1/aircraft/{aircraft_id}/equipment",
                json={
                    "equipment_type": " engine-control ",
                    "part_number": " PN-ab/01 ",
                    "serial_number": f"SN-{uuid4().hex[:8]}",
                },
            )
            assert create_response.status_code == 201
            created = create_response.json()
            equipment_id = UUID(created["id"])

            get_response = client.get(f"/api/v1/equipment/{equipment_id}")
            list_response = client.get(
                f"/api/v1/aircraft/{aircraft_id}/equipment?limit=50&offset=0"
            )

            duplicate_response = client.post(
                f"/api/v1/aircraft/{aircraft_id}/equipment",
                json={
                    "equipment_type": "ENGINE-CONTROL",
                    "part_number": created["part_number"],
                    "serial_number": created["serial_number"],
                },
            )

        assert created["aircraft_id"] == str(aircraft_id)
        assert created["equipment_type"] == "ENGINE-CONTROL"
        assert created["part_number"] == "PN-ab/01"

        assert get_response.status_code == 200
        assert get_response.json() == created

        assert list_response.status_code == 200
        page = list_response.json()
        assert page["total"] == 1
        assert page["items"] == [created]

        assert duplicate_response.status_code == 409
        assert duplicate_response.json()["error"]["code"] == "equipment_already_exists"
    finally:
        asyncio.run(cleanup(aircraft_ids))


def test_retired_aircraft_rejects_equipment_registration() -> None:
    aircraft_ids: set[UUID] = set()

    try:
        with TestClient(create_app()) as client:
            aircraft_response = client.post(
                "/api/v1/aircraft",
                json={"registration": registration("RT")},
            )
            assert aircraft_response.status_code == 201
            aircraft_id = UUID(aircraft_response.json()["id"])
            aircraft_ids.add(aircraft_id)

            retired = client.post(f"/api/v1/aircraft/{aircraft_id}/retire")
            assert retired.status_code == 200

            response = client.post(
                f"/api/v1/aircraft/{aircraft_id}/equipment",
                json={
                    "equipment_type": "ENGINE-CONTROL",
                    "part_number": "PN-RET-001",
                    "serial_number": f"SN-{uuid4().hex[:8]}",
                },
            )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == ("aircraft_retired_for_equipment_registration")
    finally:
        asyncio.run(cleanup(aircraft_ids))


def test_equipment_read_endpoints_return_not_found_for_unknown_resources() -> None:
    unknown_aircraft_id = uuid4()
    unknown_equipment_id = uuid4()

    with TestClient(create_app()) as client:
        aircraft_response = client.get(f"/api/v1/aircraft/{unknown_aircraft_id}/equipment")
        equipment_response = client.get(f"/api/v1/equipment/{unknown_equipment_id}")

    assert aircraft_response.status_code == 404
    assert aircraft_response.json()["error"]["code"] == "aircraft_not_found"

    assert equipment_response.status_code == 404
    assert equipment_response.json()["error"]["code"] == "equipment_not_found"
