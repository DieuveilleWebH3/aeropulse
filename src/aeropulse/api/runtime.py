"""Runtime resource contracts used by the HTTP composition root."""

from collections.abc import Callable
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from aeropulse.settings import Settings


class RuntimeResources(Protocol):
    """Lifecycle and dependency contract for application-wide technical resources."""

    def create_database_session(self) -> AsyncSession:
        """Create one caller-owned database session."""
        ...

    async def is_ready(self) -> bool:
        """Return whether all critical runtime dependencies are currently ready."""
        ...

    async def close(self) -> None:
        """Release all resources owned by this manager."""
        ...


type RuntimeResourcesFactory = Callable[[Settings], RuntimeResources]
