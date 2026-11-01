"""Aircraft aggregate root."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from aeropulse.fleet.domain.value_objects import AircraftRegistration


class AircraftStatus(StrEnum):
    """Lifecycle states currently supported for an aircraft."""

    ACTIVE = "active"
    RETIRED = "retired"


def _normalize_aware_datetime(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"aircraft {field_name} must be timezone-aware")
    return value.astimezone(UTC)


class Aircraft:
    """Aircraft aggregate root with explicit lifecycle behavior."""

    __slots__ = (
        "_created_at",
        "_id",
        "_registration",
        "_retired_at",
        "_status",
    )

    def __init__(
        self,
        *,
        id: UUID,
        registration: AircraftRegistration,
        created_at: datetime,
    ) -> None:
        self._id = id
        self._registration = registration
        self._created_at = _normalize_aware_datetime(
            created_at,
            field_name="created_at",
        )
        self._status = AircraftStatus.ACTIVE
        self._retired_at: datetime | None = None

    @classmethod
    def rehydrate(
        cls,
        *,
        id: UUID,
        registration: AircraftRegistration,
        status: AircraftStatus,
        created_at: datetime,
        retired_at: datetime | None,
    ) -> Self:
        """Restore an Aircraft from trusted persisted state."""
        aircraft = cls(
            id=id,
            registration=registration,
            created_at=created_at,
        )

        normalized_retired_at = (
            None
            if retired_at is None
            else _normalize_aware_datetime(
                retired_at,
                field_name="retired_at",
            )
        )

        if status is AircraftStatus.ACTIVE and normalized_retired_at is not None:
            raise ValueError("active aircraft must not have retired_at")
        if status is AircraftStatus.RETIRED and normalized_retired_at is None:
            raise ValueError("retired aircraft must have retired_at")
        if normalized_retired_at is not None and normalized_retired_at < aircraft.created_at:
            raise ValueError("aircraft retired_at must not precede created_at")

        aircraft._status = status
        aircraft._retired_at = normalized_retired_at
        return aircraft

    def retire(self, *, retired_at: datetime) -> bool:
        """Retire an active aircraft.

        Returns:
            True when this call changed the lifecycle state.
            False when the aircraft was already retired.
        """
        if self._status is AircraftStatus.RETIRED:
            return False

        normalized_retired_at = _normalize_aware_datetime(
            retired_at,
            field_name="retired_at",
        )
        if normalized_retired_at < self._created_at:
            raise ValueError("aircraft retired_at must not precede created_at")

        self._status = AircraftStatus.RETIRED
        self._retired_at = normalized_retired_at
        return True

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

    @property
    def retired_at(self) -> datetime | None:
        """Return the UTC retirement timestamp, if retired."""
        return self._retired_at
