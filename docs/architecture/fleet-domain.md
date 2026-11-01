# AeroPulse — Fleet Domain: Aircraft Registration

**Ticket:** S1-001 — Aircraft Domain Model & Registration Use Case
**Sprint:** 1 — Fleet & Asset Management
**Status:** Accepted for implementation

## 1. Purpose

S1-001 introduces AeroPulse's first business bounded-context implementation.

The ticket models aircraft registration independently from HTTP, SQLAlchemy, PostgreSQL, and other
infrastructure.

The deliverable is a pure domain/application foundation:

```text
RegisterAircraftCommand
        |
        v
RegisterAircraftHandler
        |
        +--> AircraftRegistration invariant
        |
        +--> AircraftRepository port
        |
        v
Aircraft aggregate
```

Persistence and HTTP delivery are intentionally deferred to S1-002 and S1-003.

## 2. Business Goal

A Fleet operator must be able to register an aircraft exactly once under one canonical registration.

AeroPulse needs a stable aircraft identity before later capabilities can attach equipment, sensors,
telemetry, anomalies, maintenance recommendations, and audit history.

## 3. V1 Aircraft Model

An aircraft contains:

```text
id
registration
status
created_at
```

A newly registered aircraft is always `ACTIVE`.

`RETIRED` is reserved for a later lifecycle story and cannot be supplied arbitrarily during
registration. No hard-delete behavior is introduced.

## 4. Registration V1 Policy

The registration value object:

1. trims surrounding whitespace;
2. uppercases the value;
3. rejects empty values;
4. limits the canonical value to 16 characters;
5. accepts alphanumeric groups separated by single hyphens.

Examples:

```text
F-HABC   -> F-HABC
 f-habc  -> F-HABC
N123AB   -> N123AB
G-ABCD   -> G-ABCD
```

Rejected examples:

```text
F HABC
F/HABC
F--HABC
-F-HABC
F-HABC-
```

This rule is an **AeroPulse demonstrator policy**. It is not presented as a complete or certified
validator for every civil, military, experimental, historic, or country-specific registration
scheme worldwide.

If a real operator later requires jurisdiction-specific validation, that should be introduced from
authoritative rules and explicit requirements.

## 5. Canonical Equality

Duplicate detection operates on the canonical value. Therefore `F-HABC`, `f-habc`, and
`" F-HABC "` represent the same registration.

Normalization happens before repository lookup.

## 6. Aggregate Invariants

### Status

Aircraft are active on first registration. The application cannot create a retired aircraft by
passing a constructor status.

The aircraft ID, canonical registration, and creation timestamp are exposed through read-only
properties. Registration cannot be reassigned by ordinary application code. Lifecycle transitions
will later be domain methods rather than raw field mutation.

### Created time

`created_at` must be timezone-aware. The aggregate normalizes it to UTC. A naive datetime is
rejected.

## 7. Register Aircraft Use Case

Input:

```python
RegisterAircraftCommand(registration="F-HABC")
```

Flow:

```text
raw registration
      |
      v
canonical AircraftRegistration
      |
      v
repository.exists_by_registration()
      |
      +-- true --> AircraftRegistrationAlreadyExists
      |
      v
generate UUID
      |
      v
obtain UTC time
      |
      v
create active Aircraft
      |
      v
repository.add()
      |
      v
return Aircraft
```

## 8. Dependency Inversion

The application depends on the `AircraftRepository` protocol. It does not depend on SQLAlchemy,
PostgreSQL, FastAPI, or Redis.

S1-002 will implement the repository port using PostgreSQL/SQLAlchemy.

## 9. ID and Time Injection

The handler accepts two small callable dependencies: `id_generator` and `clock`.

Production defaults use UUID4 and current UTC time. Tests inject deterministic values.

This avoids monkey-patching and avoids introducing a generic ID/time framework before it is needed.

## 10. Duplicate Registration and Concurrency

S1-001 performs an application-level duplicate lookup because it enables the useful business error
`AircraftRegistrationAlreadyExists`.

This does **not** make registration concurrency-safe.

Unsafe race:

```text
request A -> exists? false
request B -> exists? false
request A -> add
request B -> add
```

Therefore S1-002 must add a PostgreSQL uniqueness invariant on the canonical registration column:

```sql
UNIQUE (registration)
```

The application check improves behavior; the database constraint protects integrity. Both are
needed.

## 11. Errors

Domain error:

```text
InvalidAircraftRegistration
```

Application error:

```text
AircraftRegistrationAlreadyExists
```

S1-001 deliberately does not create a generic global business-error framework. S1-003 can map the
duplicate application error to HTTP `409 Conflict` when the HTTP API exists.

## 12. Non-goals

S1-001 does not add SQLAlchemy tables, Alembic, a PostgreSQL repository implementation, HTTP
endpoints, Pydantic request/response models, pagination, aircraft update/retirement, equipment,
telemetry, or audit records.

## 13. Testing Strategy

All S1-001 tests are unit tests. Coverage includes registration normalization and invalid values,
maximum length, canonical representation, active status, UTC normalization, naive timestamp
rejection, deterministic ID/time injection, repository persistence, duplicate rejection, and
validation-before-persistence behavior.

No database or HTTP test is justified yet.

## 14. Risks and Mitigations

### Registration policy treated as globally authoritative

**Risk:** legitimate jurisdiction-specific formats could be rejected.

**Mitigation:** document the rule as an AeroPulse V1 platform policy, not an international registry
specification.

### Duplicate race condition

**Risk:** concurrent requests can both pass the application pre-check.

**Mitigation:** S1-002 adds a database unique constraint and translates uniqueness violations back to
the application error.

### Domain coupled to persistence

**Risk:** database schema starts dictating business design.

**Mitigation:** implement pure domain/application behavior first and depend on a repository port.

### Excessive DDD abstraction

**Risk:** boilerplate hides simple business behavior.

**Mitigation:** introduce only one meaningful value object, one aggregate, one repository port, one
command, and one handler.

## 15. Definition of Done

S1-001 is complete when:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

all pass, CI is green, and there is no FastAPI/SQLAlchemy/Redis/AWS import inside
`aeropulse.fleet.domain` or `aeropulse.fleet.application`.


## Persistence Implementation

S1-002 implements `AircraftRepository` in:

```text
aeropulse.fleet.infrastructure.persistence
```

The adapter uses SQLAlchemy Core and PostgreSQL while keeping domain/application modules free of
SQLAlchemy imports.

Registration uniqueness now has two layers:

```text
application pre-check
        +
PostgreSQL UNIQUE constraint
```

The first provides useful business behavior; the second protects integrity under concurrency.
