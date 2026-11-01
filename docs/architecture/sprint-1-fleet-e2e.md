# Sprint 1 — Fleet Integration & E2E Validation

**Ticket:** S1-008 — Fleet integration & E2E validation
**Sprint:** 1 — Fleet & Asset Management

## Purpose

S1-008 closes Sprint 1 by proving that the Fleet capabilities implemented in S1-001 through
S1-007 work together as one assembled system.

This ticket deliberately adds no new Fleet business capability, no migration, and no runtime
dependency. Its purpose is integration confidence.

## Scope under test

The completed Sprint 1 slice is:

```text
readiness
    ↓
register Aircraft
    ↓
retrieve/list Aircraft
    ↓
register Equipment on ACTIVE Aircraft
    ↓
retrieve/list Equipment
    ↓
retire Aircraft
    ↓
repeat retirement safely
    ↓
keep existing Equipment readable
    ↓
reject new Equipment on RETIRED Aircraft
```

A second scenario proves the fleet-wide physical Equipment identity rule:

```text
Aircraft A owns (part_number, serial_number)
    ↓
Aircraft B attempts same physical identity
    ↓
409 equipment_already_exists
```

## Test boundary

The E2E assertions are intentionally black-box.

Tests use:

```text
TestClient
    ↓
create_app()
    ↓
FastAPI presentation
    ↓
application handlers
    ↓
domain
    ↓
SQLAlchemy adapters
    ↓
PostgreSQL
```

`/ready` also exercises the configured runtime dependency readiness path, including Redis.

Test assertions use public HTTP responses only. Direct SQL access is used only after each
scenario to remove test-created rows; database implementation details are not used to prove
business outcomes.

## Why this does not replace lower-level tests

E2E validates assembly, not every edge case.

Sprint 1 keeps the existing test layers:

```text
domain unit
    -> invariants and value objects

application unit
    -> orchestration and business outcomes

persistence integration
    -> SQL constraints, transactions, concurrency, rehydration

HTTP contract/integration
    -> status codes, schemas, stable error envelopes

E2E
    -> complete user-visible workflows across assembled layers
```

A failure should be diagnosed at the lowest layer that can explain it rather than adding more
assertions to the E2E scenario.

## Pytest marker

S1-008 registers:

```text
e2e
```

because AeroPulse runs pytest with `--strict-markers`.

The E2E module is also marked:

```text
external_services
```

and remains gated by:

```text
AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1
```

## Local execution

Start dependencies and ensure the schema is current:

```bash
docker compose up -d
uv run --locked --group migration alembic upgrade head
uv run --locked --group migration alembic check
```

PowerShell:

```powershell
$env:AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS = "1"
uv run --locked pytest -m e2e --no-cov
```

Bash:

```bash
export AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1
uv run --locked pytest -m e2e --no-cov
```

E2E-only coverage diagnostic:

```bash
uv run --locked pytest -m e2e --cov-fail-under=0
```

This report is informative. The authoritative `coverage >= 90%` requirement is evaluated against
the complete regression suite, because a narrow E2E selection intentionally does not execute every
unit/error/concurrency branch.

Run the complete regression suite afterward:

```bash
uv run --locked pytest
```

## Acceptance scenarios

### Scenario A — complete Fleet lifecycle

The E2E test proves:

- application readiness is available;
- an Aircraft can be registered;
- the Aircraft is initially `active`;
- two Equipment items can be registered;
- Aircraft retrieval and Fleet listing expose the created Aircraft;
- Equipment retrieval and nested listing expose both items;
- Aircraft retirement succeeds;
- repeated retirement is idempotent and preserves `retired_at`;
- the retired state remains visible through normal retrieval;
- existing Equipment remains readable after Aircraft retirement;
- new Equipment registration against the retired Aircraft is rejected with `409`.

### Scenario B — fleet-wide physical identity

The second E2E test proves:

- two distinct active Aircraft can be registered;
- a physical `(part_number, serial_number)` identity can be attached to the first;
- attaching that same identity to the second returns `409 equipment_already_exists`;
- the rejected Equipment does not appear in the second Aircraft's collection.

## Database and migration impact

None.

The expected Alembic head remains:

```text
20261101_0005
```

`uv.lock` should also remain unchanged because S1-008 adds no dependency.

## Sprint 1 completion gate

Before Sprint 1 is considered complete:

```bash
uv lock --check
uv run --locked --group migration alembic current
uv run --locked --group migration alembic check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

With external services enabled, additionally run:

```bash
uv run --locked pytest -m e2e --no-cov
```

Required outcomes:

```text
Alembic head = 20261101_0005
no pending Alembic operations
Ruff = pass
formatting = pass
strict mypy = pass
pytest = pass
coverage >= 90%
E2E = pass
```

## Sprint 1 delivered capability

Sprint 1 now provides a coherent Fleet & Asset Management foundation:

- Aircraft registration and canonical identity;
- PostgreSQL persistence and migrations;
- Aircraft retrieval/listing;
- explicit ACTIVE -> RETIRED lifecycle;
- idempotent retirement;
- Equipment domain and persistence;
- Aircraft/Equipment referential integrity;
- fleet-wide Equipment physical identity;
- Equipment HTTP registration/retrieval/listing;
- stable HTTP business-error contracts;
- race protection between retirement and Equipment attachment;
- end-to-end validation of the assembled Fleet slice.

This is the stable business foundation for later telemetry and PHM capabilities.
