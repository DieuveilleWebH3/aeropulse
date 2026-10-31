"""Live integration test for Docker Compose PostgreSQL and Redis services."""

import asyncio
import os

import pytest

from aeropulse.platform.resources import create_runtime_resources
from aeropulse.settings import load_settings

pytestmark = [
    pytest.mark.external_services,
    pytest.mark.skipif(
        os.getenv("AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS") != "1",
        reason="set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1 to test live dependencies",
    ),
]


def test_runtime_resources_connect_to_postgres_and_redis() -> None:
    async def scenario() -> None:
        resources = create_runtime_resources(load_settings())
        try:
            assert await resources.is_ready() is True
        finally:
            await resources.close()

    asyncio.run(scenario())
