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

API_SUMMARY = "Aircraft predictive maintenance and fleet health engineering platform"
API_DESCRIPTION = """
AeroPulse is a production-oriented engineering demonstrator for aircraft Fleet and
Prognostics & Health Management (PHM) capabilities.

Sprint 1 exposes the Fleet foundation:

- register, retrieve, list, and retire Aircraft;
- register, retrieve, and list maintainable Equipment;
- enforce aircraft lifecycle and physical Equipment identity invariants;
- expose stable HTTP business-error contracts.

Later sprints will build telemetry ingestion, health scoring, anomaly detection,
degradation/RUL analysis, maintenance recommendations, auditability, security,
observability, and cloud deployment on top of this foundation.

**Important:** AeroPulse uses synthetic/public engineering data and is not a certified
airworthiness, flight-safety, or maintenance-decision system.
"""
OPENAPI_TAGS = [
    {
        "name": "aircraft",
        "description": ("Aircraft identity, Fleet retrieval, and explicit lifecycle operations."),
    },
    {
        "name": "equipment",
        "description": (
            "Maintainable Equipment registration and retrieval scoped to Fleet Aircraft."
        ),
    },
]
SWAGGER_UI_PARAMETERS = {
    "deepLinking": True,
    "displayRequestDuration": True,
    "docExpansion": "list",
    "filter": True,
    "persistAuthorization": True,
    "tryItOutEnabled": True,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Create and release application-wide runtime resources."""
    settings = cast(Settings, app.state.settings)
    resources_factory = cast(
        RuntimeResourcesFactory,
        app.state.runtime_resources_factory,
    )
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
        summary=API_SUMMARY,
        description=API_DESCRIPTION,
        version=version("aeropulse"),
        debug=resolved_settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=OPENAPI_TAGS,
        license_info={
            "name": "MIT",
            "identifier": "MIT",
        },
        swagger_ui_parameters=SWAGGER_UI_PARAMETERS,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.runtime_resources = None
    app.state.runtime_resources_factory = runtime_resources_factory

    register_fleet_exception_handlers(app)
    app.include_router(system_router)
    app.include_router(fleet_router)
    return app
