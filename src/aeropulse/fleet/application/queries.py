"""Query objects and read results for Fleet aircraft use cases."""

from dataclasses import dataclass
from uuid import UUID

from aeropulse.fleet.domain.aircraft import Aircraft

DEFAULT_AIRCRAFT_PAGE_SIZE = 50
MAX_AIRCRAFT_PAGE_SIZE = 100


@dataclass(frozen=True, slots=True)
class GetAircraftQuery:
    """Request one aircraft by its stable identifier."""

    aircraft_id: UUID


@dataclass(frozen=True, slots=True)
class ListAircraftQuery:
    """Request one offset-based aircraft page."""

    limit: int = DEFAULT_AIRCRAFT_PAGE_SIZE
    offset: int = 0

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= MAX_AIRCRAFT_PAGE_SIZE:
            raise ValueError(f"aircraft page limit must be between 1 and {MAX_AIRCRAFT_PAGE_SIZE}")
        if self.offset < 0:
            raise ValueError("aircraft page offset must be non-negative")


@dataclass(frozen=True, slots=True)
class AircraftPage:
    """Application-level paginated aircraft result."""

    items: tuple[Aircraft, ...]
    total: int
    limit: int
    offset: int
