"""Add maintainable equipment persistence.

Revision ID: 20261101_0005
Revises: 20261101_0004
Create Date: 2026-11-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261101_0005"
down_revision: str | None = "20261101_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the equipment table, identity constraint, FK, and listing index."""
    op.create_table(
        "equipment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("aircraft_id", sa.Uuid(), nullable=False),
        sa.Column("equipment_type", sa.String(length=32), nullable=False),
        sa.Column("part_number", sa.String(length=32), nullable=False),
        sa.Column("serial_number", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(trim(equipment_type)) > 0 "
            "AND length(trim(part_number)) > 0 "
            "AND length(trim(serial_number)) > 0",
            name=op.f("ck_equipment_required_values"),
        ),
        sa.ForeignKeyConstraint(
            ["aircraft_id"],
            ["aircraft.id"],
            name=op.f("fk_equipment_aircraft_id_aircraft"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_equipment")),
        sa.UniqueConstraint(
            "part_number",
            "serial_number",
            name=op.f("uq_equipment_part_number_serial_number"),
        ),
    )
    op.create_index(
        op.f("ix_equipment_aircraft_created_at_id"),
        "equipment",
        ["aircraft_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop maintainable equipment persistence."""
    op.drop_index(op.f("ix_equipment_aircraft_created_at_id"), table_name="equipment")
    op.drop_table("equipment")
