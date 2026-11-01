"""Aircraft aggregate root."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from aeropulse.fleet.domain.value_objects import AircraftRegistration


class AircraftStatus(StrEnum):
    """Lifecycle states currently supported for an aircraft."""

    ACTIVE = "active"
    RETIRED = "retired"


class Aircraft:
    """Aircraft aggregate root with read-only registration identity data.

    Aircraft are always active when first registered. Lifecycle transitions are added
    through explicit domain behavior in later stories rather than by exposing status
    or registration as arbitrary mutable fields.
    """

    __slots__ = ("_created_at", "_id", "_registration", "_status")

    def __init__(
        self,
        *,
        id: UUID,
        registration: AircraftRegistration,
        created_at: datetime,
    ) -> None:
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError("aircraft created_at must be timezone-aware")

        self._id = id
        self._registration = registration
        self._created_at = created_at.astimezone(UTC)
        self._status = AircraftStatus.ACTIVE

    @property
    def id(self) -> UUID:
        """Return the stable aircraft identifier."""
        return self._id

    @property
    def registration(self) -> AircraftRegistration:
        """Return the immutable canonical aircraft registration."""
        return self._registration

    @property
    def created_at(self) -> datetime:
        """Return the UTC registration timestamp."""
        return self._created_at

    @property
    def status(self) -> AircraftStatus:
        """Return the current aircraft lifecycle state."""
        return self._status
