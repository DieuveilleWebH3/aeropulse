"""Immutable telemetry sample domain model."""

import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from aeropulse.telemetry.domain.errors import (
    InvalidTelemetryEquipmentId,
    InvalidTelemetryId,
    InvalidTelemetryMetric,
    InvalidTelemetryTimestamp,
    InvalidTelemetryUnit,
    InvalidTelemetryValue,
)

_METRIC_PATTERN = re.compile(r"[a-z][a-z0-9_]*\Z")
_MAX_METRIC_LENGTH = 64
_MAX_UNIT_LENGTH = 24


def _canonical_metric(value: str) -> str:
    if not isinstance(value, str):
        raise InvalidTelemetryMetric("telemetry metric must be a string")
    if any(ord(character) <= 0x1F or ord(character) == 0x7F for character in value):
        raise InvalidTelemetryMetric("telemetry metric must not contain ASCII control characters")

    normalized = value.strip().lower()
    if not normalized:
        raise InvalidTelemetryMetric("telemetry metric must not be empty")
    if len(normalized) > _MAX_METRIC_LENGTH:
        raise InvalidTelemetryMetric(
            f"telemetry metric must be at most {_MAX_METRIC_LENGTH} characters"
        )
    if _METRIC_PATTERN.fullmatch(normalized) is None:
        raise InvalidTelemetryMetric(
            "telemetry metric must start with a lowercase letter and contain only "
            "letters, digits, and underscores"
        )
    return normalized


def _finite_value(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidTelemetryValue("telemetry value must be a finite floating-point number")

    try:
        normalized = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise InvalidTelemetryValue(
            "telemetry value could not be converted to a finite floating-point number"
        ) from exc
    if not math.isfinite(normalized):
        raise InvalidTelemetryValue("telemetry value must be finite")
    return normalized


def _canonical_unit(value: str) -> str:
    if not isinstance(value, str):
        raise InvalidTelemetryUnit("telemetry unit must be a string")
    if any(ord(character) <= 0x1F or ord(character) == 0x7F for character in value):
        raise InvalidTelemetryUnit("telemetry unit must not contain ASCII control characters")

    normalized = value.strip()
    if not normalized:
        raise InvalidTelemetryUnit("telemetry unit must not be empty")
    if len(normalized) > _MAX_UNIT_LENGTH:
        raise InvalidTelemetryUnit(f"telemetry unit must be at most {_MAX_UNIT_LENGTH} characters")
    return normalized


def _utc_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidTelemetryTimestamp("telemetry observed_at must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidTelemetryTimestamp("telemetry observed_at must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class TelemetrySample:
    """One immutable, validated equipment telemetry measurement."""

    id: UUID
    equipment_id: UUID
    metric: str
    value: float
    unit: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise InvalidTelemetryId("telemetry sample id must be a UUID")
        if not isinstance(self.equipment_id, UUID):
            raise InvalidTelemetryEquipmentId("telemetry equipment_id must be a UUID")

        object.__setattr__(self, "metric", _canonical_metric(self.metric))
        object.__setattr__(self, "value", _finite_value(self.value))
        object.__setattr__(self, "unit", _canonical_unit(self.unit))
        object.__setattr__(self, "observed_at", _utc_timestamp(self.observed_at))
