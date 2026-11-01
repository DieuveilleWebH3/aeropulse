"""PostgreSQL integration tests for Equipment persistence."""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import delete, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from aeropulse.fleet.domain.equipment import Equipment
from aeropulse.fleet.domain.repositories import EquipmentIdentityConflict
from aeropulse.fleet.domain.value_objects import (
    EquipmentPartNumber,
    EquipmentSerialNumber,
    EquipmentType,
)
from aeropulse.fleet.infrastructure.persistence.equipment_repository import (
    SqlAlchemyEquipmentRepository,
)
from aeropulse.fleet.infrastructure.persistence.schema import aircraft_table, equipment_table
from aeropulse.settings import load_settings

pytestmark = [
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to test PostgreSQL persistence",
    ),
]

AIRCRAFT_ID = UUID("30000000-0000-4000-8000-000000000001")
EQUIPMENT_ID_1 = UUID("40000000-0000-4000-8000-000000000001")
EQUIPMENT_ID_2 = UUID("40000000-0000-4000-8000-000000000002")
CREATED_AT = datetime(2002, 1, 1, 10, 0, tzinfo=UTC)


async def cleanup() -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            await connection.execute(
                delete(equipment_table).where(equipment_table.c.aircraft_id == AIRCRAFT_ID)
            )
            await connection.execute(
                delete(aircraft_table).where(aircraft_table.c.id == AIRCRAFT_ID)
            )
    finally:
        await engine.dispose()


async def seed_aircraft() -> None:
    settings = load_settings()
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        async with engine.begin() as connection:
            await connection.execute(
                insert(aircraft_table).values(
                    id=AIRCRAFT_ID,
                    registration="EQ-TEST",
                    status="active",
                    created_at=CREATED_AT - timedelta(days=1),
                    retired_at=None,
                )
            )
    finally:
        await engine.dispose()


def make_equipment(
    *,
    equipment_id: UUID,
    part_number: str,
    serial_number: str,
    created_at: datetime,
    aircraft_id: UUID = AIRCRAFT_ID,
) -> Equipment:
    return Equipment(
        id=equipment_id,
        aircraft_id=aircraft_id,
        equipment_type=EquipmentType("ENGINE"),
        part_number=EquipmentPartNumber(part_number),
        serial_number=EquipmentSerialNumber(serial_number),
        created_at=created_at,
    )


def test_repository_persists_reads_lists_and_counts_equipment() -> None:
    async def scenario() -> None:
        await cleanup()
        await seed_aircraft()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        first = make_equipment(
            equipment_id=EQUIPMENT_ID_1,
            part_number="PN-A",
            serial_number="SN-001",
            created_at=CREATED_AT,
        )
        second = make_equipment(
            equipment_id=EQUIPMENT_ID_2,
            part_number="PN-B",
            serial_number="SN-001",
            created_at=CREATED_AT + timedelta(minutes=1),
        )

        try:
            async with session_factory.begin() as session:
                repository = SqlAlchemyEquipmentRepository(session)
                await repository.add(second)
                await repository.add(first)

            async with session_factory() as session:
                repository = SqlAlchemyEquipmentRepository(session)
                loaded = await repository.get_by_id(EQUIPMENT_ID_1)
                page = await repository.list_by_aircraft(AIRCRAFT_ID, limit=10, offset=0)
                count = await repository.count_by_aircraft(AIRCRAFT_ID)

            assert loaded is not None
            assert loaded.part_number.value == "PN-A"
            assert [item.id for item in page] == [EQUIPMENT_ID_1, EQUIPMENT_ID_2]
            assert count == 2
        finally:
            await engine.dispose()
            await cleanup()

    asyncio.run(scenario())


def test_repository_enforces_composite_equipment_identity() -> None:
    async def scenario() -> None:
        await cleanup()
        await seed_aircraft()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        try:
            async with session_factory.begin() as session:
                await SqlAlchemyEquipmentRepository(session).add(
                    make_equipment(
                        equipment_id=EQUIPMENT_ID_1,
                        part_number="PN-A",
                        serial_number="SN-001",
                        created_at=CREATED_AT,
                    )
                )

            with pytest.raises(EquipmentIdentityConflict):
                async with session_factory.begin() as session:
                    await SqlAlchemyEquipmentRepository(session).add(
                        make_equipment(
                            equipment_id=EQUIPMENT_ID_2,
                            part_number="PN-A",
                            serial_number="SN-001",
                            created_at=CREATED_AT + timedelta(minutes=1),
                        )
                    )
        finally:
            await engine.dispose()
            await cleanup()

    asyncio.run(scenario())


def test_database_rejects_equipment_for_unknown_aircraft() -> None:
    async def scenario() -> None:
        await cleanup()
        settings = load_settings()
        engine = create_async_engine(settings.database_url.get_secret_value())
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        unknown_aircraft = UUID("30000000-0000-4000-8000-000000000099")

        try:
            with pytest.raises(IntegrityError):
                async with session_factory.begin() as session:
                    await SqlAlchemyEquipmentRepository(session).add(
                        make_equipment(
                            equipment_id=EQUIPMENT_ID_1,
                            part_number="PN-X",
                            serial_number="SN-X",
                            created_at=CREATED_AT,
                            aircraft_id=unknown_aircraft,
                        )
                    )
        finally:
            await engine.dispose()
            await cleanup()

    asyncio.run(scenario())
