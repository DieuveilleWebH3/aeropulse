"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version

from fastapi import FastAPI

from aeropulse.api.routes.system import router as system_router
from aeropulse.settings import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application-wide startup and shutdown state."""
    app.state.ready = True
    try:
        yield
    finally:
        app.state.ready = False


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create a configured AeroPulse FastAPI application."""
    resolved_settings = settings or Settings()

    app = FastAPI(
        title=resolved_settings.app_name,
        version=version("aeropulse"),
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    app.state.ready = False
    app.state.settings = resolved_settings
    app.include_router(system_router)
    return app
