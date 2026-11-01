"""Time source used by Fleet application use cases."""

from collections.abc import Callable
from datetime import UTC, datetime

type Clock = Callable[[], datetime]


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(UTC)
