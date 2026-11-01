"""Add deterministic aircraft listing index.

Revision ID: 20261101_0002
Revises: 20261101_0001
Create Date: 2026-11-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261101_0002"
down_revision: str | None = "20261101_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the composite index used by deterministic aircraft listing."""
    op.create_index(
        "ix_aircraft_created_at_id",
        "aircraft",
        ["created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the aircraft listing index."""
    op.drop_index(
        "ix_aircraft_created_at_id",
        table_name="aircraft",
    )
