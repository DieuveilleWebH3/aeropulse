# AeroPulse — Aircraft Lifecycle / Retirement

**Ticket:** S1-005 — Aircraft Lifecycle / Retirement
**Sprint:** 1 — Fleet & Asset Management

## Purpose

S1-005 introduces the first explicit Aircraft lifecycle transition:

```text
ACTIVE
  |
  | retire
  v
RETIRED
```

Retirement is not a generic status update and aircraft are not hard-deleted.

## Domain invariants

A newly registered aircraft is always:

```text
status = active
retired_at = null
```

A retired aircraft is always:

```text
status = retired
retired_at = timezone-aware UTC timestamp
retired_at >= created_at
```

These invariants are enforced both in the domain and in PostgreSQL.

## Domain transition

The aggregate exposes:

```python
aircraft.retire(retired_at=...)
```

The method returns:

```text
True  -> ACTIVE became RETIRED
False -> aircraft was already RETIRED
```

The first retirement timestamp is preserved permanently.

## API semantics

Endpoint:

```text
POST /api/v1/aircraft/{aircraft_id}/retire
```

First request:

```text
200 OK
status = retired
retired_at = <timestamp>
```

Repeating the request:

```text
200 OK
same retired_at
```

Retirement is intentionally idempotent at the business/API level. Clients may safely retry
after a timeout without replacing the original retirement timestamp.

Unknown aircraft:

```text
404 Not Found
```

A malformed UUID remains a FastAPI path-validation `422`.

## Concurrency protection

Persistence performs a conditional update equivalent to:

```sql
UPDATE aircraft
   SET status = 'retired',
       retired_at = :retired_at
 WHERE id = :aircraft_id
   AND status = 'active'
   AND retired_at IS NULL;
```

Exactly one concurrent request can perform the state transition.

If another request wins first, the update affects zero rows and the adapter raises
`AircraftRetirementConflict`. The application then re-reads current state:

```text
current state is RETIRED
    -> return the current aircraft as idempotent success

row no longer exists
    -> AircraftNotFound

unexpected ACTIVE state after failed conditional update
    -> propagate the technical conflict
```

This protects the original `retired_at` from later retries.

## Persistence migration

S1-004 now ends at:

```text
20261101_0003
```

where migration `0003` normalizes the historical aircraft-status check-constraint name.

S1-005 therefore introduces:

```text
20261101_0004_add_aircraft_retirement
down_revision = 20261101_0003
```

Migration `0004` adds:

```text
retired_at TIMESTAMPTZ NULL
```

and the canonical constraint:

```text
ck_aircraft_retirement_state
```

enforcing:

```sql
(status = 'active' AND retired_at IS NULL)
OR
(
    status = 'retired'
    AND retired_at IS NOT NULL
    AND retired_at >= created_at
)
```

Existing legacy `RETIRED` rows are backfilled with `created_at` before the stronger constraint
is created.

## Constraint naming

S1-004 already fixed the `ck_aircraft_status` naming-convention issue by marking the metadata
name with SQLAlchemy `conv(...)`.

S1-005 follows the same rule for:

```text
ck_aircraft_retirement_state
```

in SQLAlchemy metadata.

The Alembic migration additionally uses:

```python
op.f("ck_aircraft_retirement_state")
```

for both create and drop operations. This marks the name as final and prevents the configured
`%(constraint_name)s` naming convention from producing another doubled constraint name.

## HTTP representation

Aircraft responses now include:

```json
{
  "retired_at": null
}
```

for active aircraft and a UTC timestamp for retired aircraft.

This is an additive field to the response contract.

## Audit readiness

S1-005 records the lifecycle state required by future audit/event stories:

```text
aircraft identifier
status
retired_at
```

It deliberately does not yet introduce:

- authenticated actor identity;
- retirement reason;
- domain-event publication;
- audit table;
- transactional outbox.

Those require later identity/audit/event requirements rather than assumptions in this ticket.

## Tests

S1-005 validates:

- ACTIVE -> RETIRED domain transition;
- UTC timestamp normalization;
- idempotent repeated retirement;
- no retirement before aircraft creation;
- persisted retirement rehydration;
- conditional update concurrency behavior;
- database rejection of ACTIVE + retired_at;
- database rejection of retired_at < created_at;
- HTTP `200` retirement contract;
- `404` for an unknown aircraft;
- live POST -> retire -> GET persistence behavior;
- schema presence of `retired_at` and the retirement check constraint.

## Validation

Run:

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

Expected migration head:

```text
20261101_0004
```
