"""Live end-to-end integration tests for aircraft registration."""

import asyncio
import os
from collections.abc import Mapping
from typing import Any
from uuid import uuid4

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
    return f"T-{uuid4().hex[:8].upper()}"


async def load_aircraft_row(registration: str) -> Mapping[str, Any] | None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                select(aircraft_table).where(aircraft_table.c.registration == registration)
            )
            row = result.mappings().one_or_none()
            return None if row is None else dict(row)
    finally:
        await engine.dispose()


async def count_aircraft(registration: str) -> int:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                select(func.count())
                .select_from(aircraft_table)
                .where(aircraft_table.c.registration == registration)
            )
            return int(result.scalar_one())
    finally:
        await engine.dispose()


async def delete_aircraft(registration: str) -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            await connection.execute(
                delete(aircraft_table).where(aircraft_table.c.registration == registration)
            )
    finally:
        await engine.dispose()


def test_register_aircraft_commits_before_201_response() -> None:
    registration = unique_registration()
    raw_registration = f" {registration.lower()} "

    try:
        with TestClient(create_app()) as client:
            response = client.post(
                "/api/v1/aircraft",
                json={"registration": raw_registration},
            )

        assert response.status_code == 201
        body = response.json()
        assert body["registration"] == registration
        assert body["status"] == "active"

        persisted = asyncio.run(load_aircraft_row(registration))
        assert persisted is not None
        assert str(persisted["id"]) == body["id"]
        assert persisted["registration"] == registration
        assert persisted["status"] == "active"
    finally:
        asyncio.run(delete_aircraft(registration))


def test_duplicate_registration_returns_409_and_keeps_one_row() -> None:
    registration = unique_registration()

    try:
        with TestClient(create_app()) as client:
            first = client.post(
                "/api/v1/aircraft",
                json={"registration": registration},
            )
            duplicate = client.post(
                "/api/v1/aircraft",
                json={"registration": f" {registration.lower()} "},
            )

        assert first.status_code == 201
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == ("aircraft_registration_already_exists")
        assert asyncio.run(count_aircraft(registration)) == 1
    finally:
        asyncio.run(delete_aircraft(registration))
