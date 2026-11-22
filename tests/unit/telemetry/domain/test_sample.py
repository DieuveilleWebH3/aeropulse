"""Tests for the Telemetry sample domain model."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from aeropulse.telemetry.domain import (
    InvalidTelemetryEquipmentId,
    InvalidTelemetryId,
    InvalidTelemetryMetric,
    InvalidTelemetryTimestamp,
    InvalidTelemetryUnit,
    InvalidTelemetryValue,
    TelemetrySample,
)

SAMPLE_ID = UUID("11111111-2222-4333-8444-555555555555")
EQUIPMENT_ID = UUID("aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")


def test_valid_sample_is_canonical_immutable_and_normalized() -> None:
    source_timezone = timezone(timedelta(hours=2))
    source_timestamp = datetime(2026, 11, 22, 22, 19, tzinfo=source_timezone)
    sample = TelemetrySample(
        id=SAMPLE_ID,
        equipment_id=EQUIPMENT_ID,
        metric=" Oil_Temperature ",
        value=87.5,
        unit=" °C ",
        observed_at=source_timestamp,
    )

    assert sample.id == SAMPLE_ID
    assert sample.equipment_id == EQUIPMENT_ID
    assert sample.metric == "oil_temperature"
    assert sample.value == 87.5
    assert sample.unit == "°C"
    assert sample.observed_at == datetime(2026, 11, 22, 20, 19, tzinfo=UTC)
    assert sample.observed_at.tzinfo is UTC

    attribute_name = "metric"
    with pytest.raises(AttributeError):
        setattr(sample, attribute_name, "rpm")


@pytest.mark.parametrize(
    "metric",
    [
        "",
        "   ",
        "1temperature",
        "oil-temperature",
        "oil temperature",
        "oil.temperature",
        "oil/temperature",
        "a" * 65,
    ],
)
def test_invalid_metrics_are_rejected(metric: str) -> None:
    with pytest.raises(InvalidTelemetryMetric):
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric=metric,
            value=1.0,
            unit="rpm",
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        )


@pytest.mark.parametrize("metric", ["\nrpm", "rpm\n", "\trpm", "rpm\t", "\x00rpm", "rpm\x7f"])
def test_leading_or_trailing_metric_control_characters_are_rejected(metric: str) -> None:
    with pytest.raises(
        InvalidTelemetryMetric,
        match="must not contain ASCII control characters",
    ):
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric=metric,
            value=1.0,
            unit="rpm",
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        )


@pytest.mark.parametrize(
    "unit",
    [
        "",
        "   ",
        "u" * 25,
        "rp\nm",
        "rpm\0",
        "rpm\x7f",
    ],
)
def test_invalid_units_are_rejected(unit: str) -> None:
    with pytest.raises(InvalidTelemetryUnit):
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric="rpm",
            value=1.0,
            unit=unit,
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        )


@pytest.mark.parametrize("unit", ["\nrpm", "rpm\n", "\trpm", "rpm\t", "\x00rpm", "rpm\x7f"])
def test_leading_or_trailing_unit_control_characters_are_rejected(unit: str) -> None:
    with pytest.raises(
        InvalidTelemetryUnit,
        match="must not contain ASCII control characters",
    ):
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric="rpm",
            value=1.0,
            unit=unit,
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        )


def test_unit_preserves_case_unicode_and_accepts_length_boundaries() -> None:
    assert (
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric="rpm",
            value=1.0,
            unit="  m/s²  ",
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        ).unit
        == "m/s²"
    )

    assert (
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric="rpm",
            value=1.0,
            unit="u" * 24,
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        ).unit
        == "u" * 24
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_values_are_rejected(value: float) -> None:
    with pytest.raises(InvalidTelemetryValue, match="must be finite"):
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric="rpm",
            value=value,
            unit="rpm",
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        )


def test_huge_integer_overflow_is_rejected_as_telemetry_value() -> None:
    with pytest.raises(
        InvalidTelemetryValue,
        match="could not be converted to a finite floating-point number",
    ):
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric="rpm",
            value=10**1000,
            unit="rpm",
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        )


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(InvalidTelemetryTimestamp, match="timezone-aware"):
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id=EQUIPMENT_ID,
            metric="rpm",
            value=1.0,
            unit="rpm",
            observed_at=datetime(2026, 11, 22),
        )


def test_timezone_aware_future_timestamp_is_accepted() -> None:
    future_timestamp = datetime(2099, 1, 1, 12, 0, tzinfo=UTC)
    sample = TelemetrySample(
        id=SAMPLE_ID,
        equipment_id=EQUIPMENT_ID,
        metric="rpm",
        value=1.0,
        unit="rpm",
        observed_at=future_timestamp,
    )
    assert sample.observed_at == future_timestamp


def test_uuid_constructor_inputs_are_required() -> None:
    with pytest.raises(InvalidTelemetryId):
        TelemetrySample(
            id="not-a-uuid",  # type: ignore[arg-type]
            equipment_id=EQUIPMENT_ID,
            metric="rpm",
            value=1.0,
            unit="rpm",
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        )

    with pytest.raises(InvalidTelemetryEquipmentId):
        TelemetrySample(
            id=SAMPLE_ID,
            equipment_id="not-a-uuid",  # type: ignore[arg-type]
            metric="rpm",
            value=1.0,
            unit="rpm",
            observed_at=datetime(2026, 11, 22, tzinfo=UTC),
        )
