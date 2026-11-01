"""SQLAlchemy schema owned by the Fleet persistence adapter."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKeyConstraint,
    Index,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.schema import conv

AIRCRAFT_REGISTRATION_UNIQUE_CONSTRAINT = "uq_aircraft_registration"
AIRCRAFT_STATUS_CHECK_CONSTRAINT = "ck_aircraft_status"
AIRCRAFT_RETIREMENT_STATE_CHECK_CONSTRAINT = "ck_aircraft_retirement_state"
AIRCRAFT_LIST_INDEX = "ix_aircraft_created_at_id"
EQUIPMENT_IDENTITY_UNIQUE_CONSTRAINT = "uq_equipment_part_number_serial_number"
EQUIPMENT_REQUIRED_VALUES_CHECK_CONSTRAINT = "ck_equipment_required_values"
EQUIPMENT_AIRCRAFT_FOREIGN_KEY = "fk_equipment_aircraft_id_aircraft"
EQUIPMENT_AIRCRAFT_LIST_INDEX = "ix_equipment_aircraft_created_at_id"

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

aircraft_table = Table(
    "aircraft",
    metadata,
    Column("id", Uuid(as_uuid=True), nullable=False),
    Column("registration", String(length=16), nullable=False),
    Column("status", String(length=16), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("retired_at", DateTime(timezone=True), nullable=True),
    CheckConstraint(
        "status IN ('active', 'retired')",
        name=conv(AIRCRAFT_STATUS_CHECK_CONSTRAINT),
    ),
    CheckConstraint(
        "(status = 'active' AND retired_at IS NULL) "
        "OR (status = 'retired' AND retired_at IS NOT NULL "
        "AND retired_at >= created_at)",
        name=conv(AIRCRAFT_RETIREMENT_STATE_CHECK_CONSTRAINT),
    ),
    UniqueConstraint(
        "registration",
        name=AIRCRAFT_REGISTRATION_UNIQUE_CONSTRAINT,
    ),
    PrimaryKeyConstraint("id", name="pk_aircraft"),
)

Index(
    AIRCRAFT_LIST_INDEX,
    aircraft_table.c.created_at,
    aircraft_table.c.id,
)


equipment_table = Table(
    "equipment",
    metadata,
    Column("id", Uuid(as_uuid=True), nullable=False),
    Column("aircraft_id", Uuid(as_uuid=True), nullable=False),
    Column("equipment_type", String(length=32), nullable=False),
    Column("part_number", String(length=32), nullable=False),
    Column("serial_number", String(length=64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    CheckConstraint(
        "length(trim(equipment_type)) > 0 "
        "AND length(trim(part_number)) > 0 "
        "AND length(trim(serial_number)) > 0",
        name=conv(EQUIPMENT_REQUIRED_VALUES_CHECK_CONSTRAINT),
    ),
    ForeignKeyConstraint(
        ["aircraft_id"],
        ["aircraft.id"],
        name=EQUIPMENT_AIRCRAFT_FOREIGN_KEY,
        ondelete="RESTRICT",
    ),
    UniqueConstraint(
        "part_number",
        "serial_number",
        name=EQUIPMENT_IDENTITY_UNIQUE_CONSTRAINT,
    ),
    PrimaryKeyConstraint("id", name="pk_equipment"),
)

Index(
    EQUIPMENT_AIRCRAFT_LIST_INDEX,
    equipment_table.c.aircraft_id,
    equipment_table.c.created_at,
    equipment_table.c.id,
)
