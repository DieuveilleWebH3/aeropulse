"""Add aircraft retirement lifecycle state.

Revision ID: 20261101_0004
Revises: 20261101_0003
Create Date: 2026-11-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261101_0004"
down_revision: str | None = "20261101_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add retirement timestamp and lifecycle consistency protection."""
    op.add_column(
        "aircraft",
        sa.Column(
            "retired_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # Older S1-004 local/test data could contain RETIRED rows before
    # retirement timestamps existed. Backfill before enforcing the invariant.
    op.execute(
        sa.text(
            "UPDATE aircraft "
            "SET retired_at = created_at "
            "WHERE status = 'retired' AND retired_at IS NULL"
        )
    )

    op.create_check_constraint(
        op.f("ck_aircraft_retirement_state"),
        "aircraft",
        "(status = 'active' AND retired_at IS NULL) "
        "OR (status = 'retired' AND retired_at IS NOT NULL "
        "AND retired_at >= created_at)",
    )


def downgrade() -> None:
    """Remove retirement lifecycle persistence."""
    op.drop_constraint(
        op.f("ck_aircraft_retirement_state"),
        "aircraft",
        type_="check",
    )
    op.drop_column("aircraft", "retired_at")
