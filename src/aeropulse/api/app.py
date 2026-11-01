"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import cast

from fastapi import FastAPI

from aeropulse.api.routes.system import router as system_router
from aeropulse.api.runtime import RuntimeResourcesFactory
from aeropulse.fleet.presentation.errors import register_fleet_exception_handlers
from aeropulse.fleet.presentation.routes import router as fleet_router
from aeropulse.platform.resources import create_runtime_resources
from aeropulse.settings import Settings, load_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create and release application-wide runtime resources."""
    settings = cast(Settings, app.state.settings)
    resources_factory = cast(RuntimeResourcesFactory, app.state.runtime_resources_factory)
    resources = resources_factory(settings)
    app.state.runtime_resources = resources

    try:
        yield
    finally:
        app.state.runtime_resources = None
        await resources.close()


def create_app(
    settings: Settings | None = None,
    runtime_resources_factory: RuntimeResourcesFactory = create_runtime_resources,
) -> FastAPI:
    """Create a configured AeroPulse FastAPI application."""
    resolved_settings = settings or load_settings()

    app = FastAPI(
        title=resolved_settings.app_name,
        version=version("aeropulse"),
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.runtime_resources = None
    app.state.runtime_resources_factory = runtime_resources_factory

    register_fleet_exception_handlers(app)
    app.include_router(system_router)
    app.include_router(fleet_router)
    return app
