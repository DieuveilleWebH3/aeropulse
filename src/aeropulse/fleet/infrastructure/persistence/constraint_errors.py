"""Helpers for translating named PostgreSQL constraint failures."""

from collections.abc import Iterator

from sqlalchemy.exc import IntegrityError


def _exception_chain(exc: BaseException) -> Iterator[BaseException]:
    current: BaseException | None = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def is_named_constraint_violation(exc: IntegrityError, constraint_name: str) -> bool:
    """Return whether an integrity error names a specific database constraint."""
    return any(
        getattr(item, "constraint_name", None) == constraint_name for item in _exception_chain(exc)
    )
