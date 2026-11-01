"""Value objects owned by the Fleet domain."""

import re
from dataclasses import dataclass

from aeropulse.fleet.domain.errors import (
    InvalidAircraftRegistration,
    InvalidEquipmentPartNumber,
    InvalidEquipmentSerialNumber,
    InvalidEquipmentType,
)

_REGISTRATION_PATTERN = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)*\Z")
_MAX_REGISTRATION_LENGTH = 16


@dataclass(frozen=True, slots=True)
class AircraftRegistration:
    """Canonical aircraft registration used inside AeroPulse.

    The V1 policy is intentionally a platform invariant, not a claim to validate every
    civil or military registration scheme worldwide.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()

        if not normalized:
            raise InvalidAircraftRegistration("aircraft registration must not be empty")
        if len(normalized) > _MAX_REGISTRATION_LENGTH:
            raise InvalidAircraftRegistration(
                f"aircraft registration must be at most {_MAX_REGISTRATION_LENGTH} characters"
            )
        if _REGISTRATION_PATTERN.fullmatch(normalized) is None:
            raise InvalidAircraftRegistration(
                "aircraft registration may contain only letters, digits, and single hyphens "
                "between alphanumeric groups"
            )

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        """Return the canonical registration string."""
        return self.value


_EQUIPMENT_TYPE_PATTERN = re.compile(r"[A-Z0-9]+(?:[_-][A-Z0-9]+)*\Z")
_EQUIPMENT_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
_MAX_EQUIPMENT_TYPE_LENGTH = 32
_MAX_EQUIPMENT_PART_NUMBER_LENGTH = 32
_MAX_EQUIPMENT_SERIAL_NUMBER_LENGTH = 64


def _normalized_equipment_identifier(
    value: str,
    *,
    field_name: str,
    max_length: int,
    error_type: type[ValueError],
) -> str:
    normalized = value.strip()
    if not normalized:
        raise error_type(f"equipment {field_name} must not be empty")
    if len(normalized) > max_length:
        raise error_type(f"equipment {field_name} must be at most {max_length} characters")
    if _EQUIPMENT_IDENTIFIER_PATTERN.fullmatch(normalized) is None:
        raise error_type(f"equipment {field_name} contains unsupported characters")
    return normalized


@dataclass(frozen=True, slots=True)
class EquipmentType:
    """Canonical AeroPulse equipment classification."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not normalized:
            raise InvalidEquipmentType("equipment type must not be empty")
        if len(normalized) > _MAX_EQUIPMENT_TYPE_LENGTH:
            raise InvalidEquipmentType(
                f"equipment type must be at most {_MAX_EQUIPMENT_TYPE_LENGTH} characters"
            )
        if _EQUIPMENT_TYPE_PATTERN.fullmatch(normalized) is None:
            raise InvalidEquipmentType("equipment type contains unsupported characters")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EquipmentPartNumber:
    """Manufacturer-issued part number; case is preserved."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalized_equipment_identifier(
                self.value,
                field_name="part number",
                max_length=_MAX_EQUIPMENT_PART_NUMBER_LENGTH,
                error_type=InvalidEquipmentPartNumber,
            ),
        )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EquipmentSerialNumber:
    """Manufacturer-issued serial number; case is preserved."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            _normalized_equipment_identifier(
                self.value,
                field_name="serial number",
                max_length=_MAX_EQUIPMENT_SERIAL_NUMBER_LENGTH,
                error_type=InvalidEquipmentSerialNumber,
            ),
        )

    def __str__(self) -> str:
        return self.value
