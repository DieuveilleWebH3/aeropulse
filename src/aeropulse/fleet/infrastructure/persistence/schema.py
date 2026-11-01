"""SQLAlchemy schema owned by the Fleet persistence adapter."""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
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
AIRCRAFT_LIST_INDEX = "ix_aircraft_created_at_id"

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
    CheckConstraint(
        "status IN ('active', 'retired')",
        name=conv(AIRCRAFT_STATUS_CHECK_CONSTRAINT),
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
