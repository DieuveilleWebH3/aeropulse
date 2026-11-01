"""Tests for the AircraftRegistration value object."""

import pytest

from aeropulse.fleet.domain.errors import InvalidAircraftRegistration
from aeropulse.fleet.domain.value_objects import AircraftRegistration


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("F-HABC", "F-HABC"),
        (" f-habc ", "F-HABC"),
        ("N123AB", "N123AB"),
        ("g-abcd", "G-ABCD"),
        ("9H-ABC", "9H-ABC"),
    ],
)
def test_registration_normalizes_supported_values(raw: str, expected: str) -> None:
    assert AircraftRegistration(raw).value == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "-F-HABC",
        "F-HABC-",
        "F--HABC",
        "F HABC",
        "F/HABC",
        "F_HABC",
        "---",
    ],
)
def test_registration_rejects_invalid_shapes(raw: str) -> None:
    with pytest.raises(InvalidAircraftRegistration):
        AircraftRegistration(raw)


def test_registration_rejects_values_longer_than_v1_limit() -> None:
    with pytest.raises(
        InvalidAircraftRegistration,
        match="at most 16 characters",
    ):
        AircraftRegistration("ABCDEFGHIJKLMNOPQ")


def test_registration_string_representation_is_canonical() -> None:
    registration = AircraftRegistration(" f-habc ")

    assert str(registration) == "F-HABC"
