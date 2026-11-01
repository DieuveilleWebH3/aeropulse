"""Commands handled by the Fleet application layer."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegisterAircraftCommand:
    """Request to register one aircraft."""

    registration: str
