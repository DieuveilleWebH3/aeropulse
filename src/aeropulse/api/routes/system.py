"""Operational liveness and readiness probes."""

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Liveness probe response."""

    status: Literal["ok"] = "ok"


class ReadinessResponse(BaseModel):
    """Readiness probe response."""

    status: Literal["ready", "not_ready"]


@router.get(
    "/health",
    response_model=HealthResponse,
    include_in_schema=False,
)
async def health(response: Response) -> HealthResponse:
    """Report process liveness without checking external dependencies."""
    response.headers["Cache-Control"] = "no-store"
    return HealthResponse()


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
    include_in_schema=False,
)
async def readiness(request: Request, response: Response) -> ReadinessResponse:
    """Report whether application startup completed successfully."""
    response.headers["Cache-Control"] = "no-store"

    if not bool(getattr(request.app.state, "ready", False)):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="not_ready")

    return ReadinessResponse(status="ready")
