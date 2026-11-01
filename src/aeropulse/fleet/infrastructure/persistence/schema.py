"""SQLAlchemy schema owned by the Fleet persistence adapter."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    UniqueConstraint,
    Uuid,
)

AIRCRAFT_REGISTRATION_UNIQUE_CONSTRAINT = "uq_aircraft_registration"
AIRCRAFT_STATUS_CHECK_CONSTRAINT = "ck_aircraft_status"

metadata = MetaData()

aircraft_table = Table(
    "aircraft",
    metadata,
    Column("id", Uuid(as_uuid=True), nullable=False),
    Column("registration", String(length=16), nullable=False),
    Column("status", String(length=16), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    CheckConstraint(
        "status IN ('active', 'retired')",
        name=AIRCRAFT_STATUS_CHECK_CONSTRAINT,
    ),
    PrimaryKeyConstraint("id", name="pk_aircraft"),
    UniqueConstraint(
        "registration",
        name=AIRCRAFT_REGISTRATION_UNIQUE_CONSTRAINT,
    ),
)
