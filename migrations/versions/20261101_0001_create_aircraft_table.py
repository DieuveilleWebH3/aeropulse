"""Create aircraft table.

Revision ID: 20261101_0001
Revises:
Create Date: 2026-11-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261101_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Fleet aircraft table and integrity constraints."""
    op.create_table(
        "aircraft",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("registration", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'retired')",
            name="ck_aircraft_status",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_aircraft"),
        sa.UniqueConstraint(
            "registration",
            name="uq_aircraft_registration",
        ),
    )


def downgrade() -> None:
    """Remove the Fleet aircraft table."""
    op.drop_table("aircraft")
