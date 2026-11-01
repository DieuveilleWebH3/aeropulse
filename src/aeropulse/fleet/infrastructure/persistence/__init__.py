"""PostgreSQL persistence adapters for the Fleet bounded context."""

from aeropulse.fleet.infrastructure.persistence.repository import (
    SqlAlchemyAircraftRepository,
)

__all__ = ["SqlAlchemyAircraftRepository"]
