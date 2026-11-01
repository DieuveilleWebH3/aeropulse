"""Value objects owned by the Fleet domain."""

import re
from dataclasses import dataclass

from aeropulse.fleet.domain.errors import InvalidAircraftRegistration

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
