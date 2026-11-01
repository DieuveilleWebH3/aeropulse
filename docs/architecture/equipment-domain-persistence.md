# AeroPulse — Equipment Domain & Persistence

**Ticket:** S1-006 — Equipment Domain & Persistence
**Sprint:** 1 — Fleet & Asset Management

## Purpose

S1-006 introduces maintainable equipment attached to aircraft while keeping HTTP
exposure for S1-007.

The slice is:

```text
RegisterEquipmentCommand
        ↓
Equipment value-object validation
        ↓
lock target Aircraft row
        ↓
Aircraft exists and is ACTIVE
        ↓
equipment identity duplicate check
        ↓
Equipment aggregate creation
        ↓
PostgreSQL persistence
```

## Equipment identity

A physical equipment instance is identified by the pair:

```text
(part_number, serial_number)
```

A serial number alone is deliberately **not** assumed globally unique across every
manufacturer and part family.

Database constraint:

```text
uq_equipment_part_number_serial_number
```

Part numbers and serial numbers have surrounding whitespace removed but preserve
manufacturer-supplied case. AeroPulse does not silently change an external identifier.

`equipment_type` is an AeroPulse-owned classification and is normalized to uppercase.
Examples include:

```text
ENGINE
APU
BATTERY
LANDING_GEAR
ENGINE-CONTROL
```

The V1 type is intentionally extensible rather than a hard-coded enum because the PHM
scope will grow as datasets and equipment families are introduced.

## Aggregate

`Equipment` owns:

```text
id
 aircraft_id
 equipment_type
 part_number
 serial_number
 created_at
```

S1-006 does not invent equipment retirement, removal, installation history, position,
ATA chapter, manufacturer, maintenance interval, or transfer semantics. Those require
explicit product requirements.

## Aircraft relationship

Every Equipment row belongs to one existing Aircraft through:

```text
fk_equipment_aircraft_id_aircraft
```

with `ON DELETE RESTRICT`.

AeroPulse already models Aircraft as non-hard-deleted lifecycle state, so the foreign
key is a defense-in-depth integrity rule rather than a deletion workflow.

## Retired aircraft invariant

New equipment may not be registered against a retired aircraft.

The application checks this rule, but a plain read would leave a race:

```text
request A reads ACTIVE
request B retires Aircraft
request A inserts Equipment after retirement
```

S1-006 therefore adds an aircraft repository operation using PostgreSQL
`SELECT ... FOR UPDATE` for the registration transaction.

This serializes equipment registration with the existing retirement `UPDATE`, which
also needs a row lock:

- if equipment registration locks first, it finishes before retirement;
- if retirement wins first, equipment registration waits and then observes RETIRED.

The HTTP transaction wiring arrives in S1-007, but persistence semantics are defined
here so the API layer does not need to solve the race itself.

## Persistence

Migration chain:

```text
20261101_0004  aircraft retirement
        ↓
20261101_0005  equipment persistence
```

`equipment` contains:

```text
id              UUID PRIMARY KEY
 aircraft_id     UUID NOT NULL
 equipment_type  VARCHAR(32) NOT NULL
 part_number     VARCHAR(32) NOT NULL
 serial_number   VARCHAR(64) NOT NULL
 created_at      TIMESTAMPTZ NOT NULL
```

Integrity controls:

```text
pk_equipment
fk_equipment_aircraft_id_aircraft
uq_equipment_part_number_serial_number
ck_equipment_required_values
ix_equipment_aircraft_created_at_id
```

The listing index prepares S1-007 for deterministic equipment pagination by:

```text
(aircraft_id, created_at, id)
```

## Concurrency and duplicate registration

The application performs a pre-check for a useful business response, but PostgreSQL
uniqueness is authoritative under concurrent registration.

A late database conflict is translated:

```text
EquipmentIdentityConflict
        ↓
EquipmentAlreadyExists
```

SQLAlchemy-specific errors therefore do not leak into the application/domain layers.

## Read persistence

Although S1-006 exposes no HTTP GET endpoint, the persistence adapter implements:

```text
get_by_id
list_by_aircraft
count_by_aircraft
```

because those are the immediate persistence capabilities required by S1-007. Listing
is deterministic by `created_at ASC, id ASC`.

## Non-goals

S1-006 does not add:

- Equipment HTTP endpoints;
- equipment lifecycle/history;
- telemetry linkage;
- health score or anomaly state;
- MRO/work-order mappings;
- manufacturer/ATA metadata;
- domain events or outbox publication.

## Validation

```bash
uv run --locked --group migration alembic upgrade head
uv run --locked --group migration alembic current
uv run --locked --group migration alembic check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
uv lock --check
```

Expected Alembic head:

```text
20261101_0005
```
