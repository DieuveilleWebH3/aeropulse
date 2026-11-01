# AeroPulse — Fleet Aircraft Persistence

**Ticket:** S1-002 — PostgreSQL Aircraft Persistence & Alembic
**Sprint:** 1 — Fleet & Asset Management
**Status:** Accepted for implementation

## 1. Purpose

S1-002 implements the Fleet `AircraftRepository` port using PostgreSQL and SQLAlchemy and adds
versioned schema management with Alembic.

The domain model remains framework-independent.

```text
RegisterAircraftHandler
        |
        v
AircraftRepository (domain port)
        ^
        |
SqlAlchemyAircraftRepository
        |
        v
PostgreSQL
```

## 2. Persistence Style

AeroPulse uses SQLAlchemy Core table definitions plus `AsyncSession`.

The `Aircraft` domain aggregate is **not** decorated or mapped as a SQLAlchemy ORM class.

This keeps:

- SQLAlchemy outside the domain;
- persistence representation explicit;
- domain construction independent from lazy loading/session state;
- future schema changes from dictating aggregate implementation.

S1-002 currently needs only:

```text
exists_by_registration()
add()
```

Read/query mapping is introduced when S1-004 needs retrieval.

## 3. Transaction Ownership

`SqlAlchemyAircraftRepository` receives a caller-owned `AsyncSession`.

The repository does not call:

```text
commit()
rollback()
```

A unit of work owns the transaction boundary:

```python
async with session.begin():
    repository = SqlAlchemyAircraftRepository(session)
    ...
```

This prevents repository methods from committing partial workflows independently.

SQLAlchemy `AsyncSession` is stateful and represents one transaction context; it must not be
shared across concurrent tasks.

## 4. Aircraft Table

Initial schema:

```text
aircraft
├── id           UUID         NOT NULL
├── registration VARCHAR(16)  NOT NULL
├── status       VARCHAR(16)  NOT NULL
└── created_at   TIMESTAMPTZ  NOT NULL
```

Constraints:

```text
pk_aircraft
uq_aircraft_registration
ck_aircraft_status
```

Status values currently allowed:

```text
active
retired
```

## 5. Why Registration Is Unique in PostgreSQL

S1-001 already checks:

```text
repository.exists_by_registration()
```

That check improves the normal user experience but cannot protect against concurrent requests.

Example:

```text
A -> exists? false
B -> exists? false
A -> INSERT
B -> INSERT
```

PostgreSQL therefore enforces:

```sql
UNIQUE (registration)
```

The database is the final integrity boundary.

## 6. Race Translation

The persistence adapter does not translate every `IntegrityError` into a duplicate registration.

It inspects the exception chain and only maps the named constraint:

```text
uq_aircraft_registration
```

into:

```text
AircraftRegistrationConflict
```

The application handler then maps that persistence-port conflict into the existing business-facing:

```text
AircraftRegistrationAlreadyExists
```

Unexpected integrity failures continue propagating as failures rather than being mislabeled.

## 7. Alembic

Alembic is declared in the dedicated:

```text
migration
```

dependency group.

Reason:

- the running API does not need Alembic to serve requests;
- developers/CI/deployment tooling need Alembic to manage schema state;
- migration tooling should not silently become an application runtime dependency.

Install/sync:

```bash
uv sync --locked --group migration
```

Apply migrations:

```bash
uv run --locked --group migration alembic upgrade head
```

Inspect current revision:

```bash
uv run --locked --group migration alembic current
```

Detect model/migration drift:

```bash
uv run --locked --group migration alembic check
```

## 8. Async Alembic Environment

Alembic itself exposes a synchronous command API, but its migration environment creates a
SQLAlchemy async engine and bridges migration execution with:

```text
AsyncConnection.run_sync(...)
```

This allows AeroPulse to keep asyncpg as its PostgreSQL driver rather than maintaining a second
synchronous database driver only for migrations.

## 9. Migration Rules

Every schema change must:

1. have an Alembic revision;
2. have an explicit upgrade path;
3. have a reviewed downgrade where a safe downgrade exists;
4. use stable named constraints;
5. keep application/migration compatibility in mind;
6. pass `alembic check`.

Never use application startup to call:

```text
metadata.create_all()
```

in production.

Schema evolution belongs to migrations.

## 10. Tests

S1-002 adds PostgreSQL integration coverage for:

- transaction ownership;
- visibility only after commit;
- unique registration enforcement;
- constraint-aware error translation;
- migrated primary-key constraint;
- migrated registration unique constraint;
- migrated status check constraint.

CI runs the migration before pytest and enables live external-service tests.

## 11. Risks and Mitigations

### Application pre-check mistaken for integrity protection

**Mitigation:** PostgreSQL `UNIQUE` constraint is authoritative.

### Repository commits independently

**Mitigation:** repository executes statements but caller owns transaction commit/rollback.

### Every IntegrityError becomes “duplicate”

**Mitigation:** translate only the named `uq_aircraft_registration` constraint.

### Domain polluted with SQLAlchemy

**Mitigation:** SQLAlchemy Core schema exists under Fleet infrastructure only.

### Schema and metadata drift apart

**Mitigation:** CI runs `alembic upgrade head` and `alembic check`.

### Migration tooling bloats API runtime

**Mitigation:** Alembic lives in a dedicated `migration` dependency group.

## 12. Non-goals

S1-002 does not add:

- aircraft HTTP routes;
- session dependency injection for FastAPI;
- retrieval/list APIs;
- pagination;
- retirement behavior;
- equipment persistence;
- Redis usage;
- generic Unit of Work framework.

S1-003 will compose an `AsyncSession` transaction into the aircraft registration HTTP request.

## 13. Definition of Done

S1-002 is complete when:

```bash
uv lock
uv sync --locked --group migration
uv run --locked --group migration alembic upgrade head
uv run --locked --group migration alembic check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

pass, CI is green, and two concurrent/competing attempts cannot persist the same canonical
registration because PostgreSQL enforces the unique constraint.
