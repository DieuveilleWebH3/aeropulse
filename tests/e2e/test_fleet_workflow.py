"""Sprint 1 Fleet end-to-end acceptance tests."""

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
    pytest.mark.e2e,
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to run Fleet E2E tests",
    ),
]


def _registration(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:6].upper()}"


async def _cleanup(aircraft_ids: set[UUID]) -> None:
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


def test_complete_fleet_asset_lifecycle_end_to_end() -> None:
    """Exercise the complete Sprint 1 user-visible Fleet workflow."""
    aircraft_ids: set[UUID] = set()
    serial_suffix = uuid4().hex[:8].upper()

    try:
        with TestClient(create_app()) as client:
            readiness = client.get("/ready")
            assert readiness.status_code == 200

            created_aircraft_response = client.post(
                "/api/v1/aircraft",
                json={"registration": _registration("E2E")},
            )
            assert created_aircraft_response.status_code == 201

            created_aircraft = created_aircraft_response.json()
            aircraft_id = UUID(created_aircraft["id"])
            aircraft_ids.add(aircraft_id)

            assert created_aircraft["status"] == "active"
            assert created_aircraft["retired_at"] is None

            first_equipment_response = client.post(
                f"/api/v1/aircraft/{aircraft_id}/equipment",
                json={
                    "equipment_type": "engine-control",
                    "part_number": "PN-E2E-A",
                    "serial_number": f"SN-A-{serial_suffix}",
                },
            )
            second_equipment_response = client.post(
                f"/api/v1/aircraft/{aircraft_id}/equipment",
                json={
                    "equipment_type": "hydraulic-pump",
                    "part_number": "PN-E2E-B",
                    "serial_number": f"SN-B-{serial_suffix}",
                },
            )

            assert first_equipment_response.status_code == 201
            assert second_equipment_response.status_code == 201

            first_equipment = first_equipment_response.json()
            second_equipment = second_equipment_response.json()

            assert first_equipment["aircraft_id"] == str(aircraft_id)
            assert second_equipment["aircraft_id"] == str(aircraft_id)

            retrieved_aircraft = client.get(f"/api/v1/aircraft/{aircraft_id}")
            assert retrieved_aircraft.status_code == 200
            assert retrieved_aircraft.json()["status"] == "active"

            aircraft_page = client.get("/api/v1/aircraft?limit=100&offset=0")
            assert aircraft_page.status_code == 200
            assert str(aircraft_id) in {item["id"] for item in aircraft_page.json()["items"]}

            retrieved_equipment = client.get(f"/api/v1/equipment/{first_equipment['id']}")
            assert retrieved_equipment.status_code == 200
            assert retrieved_equipment.json() == first_equipment

            equipment_page = client.get(
                f"/api/v1/aircraft/{aircraft_id}/equipment?limit=50&offset=0"
            )
            assert equipment_page.status_code == 200
            assert equipment_page.json()["total"] == 2
            assert {item["id"] for item in equipment_page.json()["items"]} == {
                first_equipment["id"],
                second_equipment["id"],
            }

            first_retirement = client.post(f"/api/v1/aircraft/{aircraft_id}/retire")
            repeated_retirement = client.post(f"/api/v1/aircraft/{aircraft_id}/retire")

            assert first_retirement.status_code == 200
            assert repeated_retirement.status_code == 200

            retired_aircraft = first_retirement.json()
            repeated_retired_aircraft = repeated_retirement.json()

            assert retired_aircraft["status"] == "retired"
            assert retired_aircraft["retired_at"] is not None
            assert repeated_retired_aircraft["retired_at"] == retired_aircraft["retired_at"]

            persisted_retired_aircraft = client.get(f"/api/v1/aircraft/{aircraft_id}")
            assert persisted_retired_aircraft.status_code == 200
            assert persisted_retired_aircraft.json()["status"] == "retired"
            assert persisted_retired_aircraft.json()["retired_at"] == retired_aircraft["retired_at"]

            equipment_after_retirement = client.get(
                f"/api/v1/aircraft/{aircraft_id}/equipment?limit=50&offset=0"
            )
            assert equipment_after_retirement.status_code == 200
            assert equipment_after_retirement.json()["total"] == 2

            blocked_registration = client.post(
                f"/api/v1/aircraft/{aircraft_id}/equipment",
                json={
                    "equipment_type": "avionics",
                    "part_number": "PN-E2E-C",
                    "serial_number": f"SN-C-{serial_suffix}",
                },
            )
            assert blocked_registration.status_code == 409
            assert blocked_registration.json()["error"]["code"] == (
                "aircraft_retired_for_equipment_registration"
            )
    finally:
        asyncio.run(_cleanup(aircraft_ids))


def test_equipment_physical_identity_is_unique_across_the_fleet() -> None:
    """Prove one physical part/serial identity cannot belong to two aircraft."""
    aircraft_ids: set[UUID] = set()
    identity_suffix = uuid4().hex[:8].upper()
    part_number = f"PN-X-{identity_suffix}"
    serial_number = f"SN-X-{identity_suffix}"

    try:
        with TestClient(create_app()) as client:
            first_aircraft_response = client.post(
                "/api/v1/aircraft",
                json={"registration": _registration("EA")},
            )
            second_aircraft_response = client.post(
                "/api/v1/aircraft",
                json={"registration": _registration("EB")},
            )

            assert first_aircraft_response.status_code == 201
            assert second_aircraft_response.status_code == 201

            first_aircraft_id = UUID(first_aircraft_response.json()["id"])
            second_aircraft_id = UUID(second_aircraft_response.json()["id"])
            aircraft_ids.update({first_aircraft_id, second_aircraft_id})

            first_registration = client.post(
                f"/api/v1/aircraft/{first_aircraft_id}/equipment",
                json={
                    "equipment_type": "engine-control",
                    "part_number": part_number,
                    "serial_number": serial_number,
                },
            )
            assert first_registration.status_code == 201

            conflicting_registration = client.post(
                f"/api/v1/aircraft/{second_aircraft_id}/equipment",
                json={
                    "equipment_type": "engine-control",
                    "part_number": part_number,
                    "serial_number": serial_number,
                },
            )

            assert conflicting_registration.status_code == 409
            assert conflicting_registration.json()["error"]["code"] == ("equipment_already_exists")

            second_aircraft_equipment = client.get(
                f"/api/v1/aircraft/{second_aircraft_id}/equipment"
            )
            assert second_aircraft_equipment.status_code == 200
            assert second_aircraft_equipment.json()["total"] == 0
            assert second_aircraft_equipment.json()["items"] == []
    finally:
        asyncio.run(_cleanup(aircraft_ids))
