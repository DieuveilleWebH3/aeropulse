"""Runtime resource contracts used by the HTTP composition root."""

from collections.abc import Callable
from typing import Protocol

from aeropulse.settings import Settings


class RuntimeResources(Protocol):
    """Lifecycle and readiness contract for application-wide technical resources."""

    async def is_ready(self) -> bool:
        """Return whether all critical runtime dependencies are currently ready."""
        ...

    async def close(self) -> None:
        """Release all resources owned by this manager."""
        ...


type RuntimeResourcesFactory = Callable[[Settings], RuntimeResources]
