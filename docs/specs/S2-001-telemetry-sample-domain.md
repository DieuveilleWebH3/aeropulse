# S2-001 — Telemetry Sample Domain Model

- Status: Implemented
- Sprint: 2 — Telemetry Ingestion Foundation
- Type: User story / domain foundation
- Primary bounded context: Telemetry
- ADRs: [ADR-001](../adr/ADR-001-spec-driven-development.md),
  [ADR-002](../adr/ADR-002-telemetry-bounded-context.md)

## User Story

As the AeroPulse telemetry ingestion layer,
I want a trustworthy domain representation of one Equipment telemetry measurement,
so that later persistence, API ingestion, and PHM processing operate on validated measurement
facts rather than raw unbounded input.

## Problem / Context

Sprint 1 created Aircraft and Equipment identity/lifecycle. Sprint 2 begins telemetry ingestion.

Before adding persistence or an HTTP ingestion endpoint, AeroPulse needs a framework-independent
domain contract for a single measurement.

This story intentionally establishes only the domain model and its unit tests. It is the first
Spec-Driven Development / Copilot-agent experiment.

## Scope

Add a new Telemetry domain package under:

```text
src/aeropulse/telemetry/domain/
```

representing one immutable telemetry sample with:

```text
id: UUID
equipment_id: UUID
metric
value
unit
observed_at
```

The exact internal file split is an implementation choice. Do not create generic abstractions
that are not needed by this story.

## Domain Invariants

### Sample identity

- `id` is a UUID supplied to the domain constructor.
- `equipment_id` is a UUID reference to the Equipment that produced the measurement.
- This story does not query Fleet or validate Equipment existence.

### Metric name

The metric is an AeroPulse-owned identifier.

Required behavior:

- trim leading/trailing whitespace;
- canonicalize to lowercase;
- length: 1..64 characters after trimming;
- first character must be `a-z`;
- remaining characters may contain only `a-z`, `0-9`, and `_`;
- reject spaces, hyphens, dots, slashes, control characters, and empty values.

Examples:

```text
" oil_temperature " -> "oil_temperature"
"RPM"               -> "rpm"
"oil-pressure"      -> invalid
"oil pressure"      -> invalid
```

### Numeric value

`value` is a floating-point measurement.

It must be finite.

Reject:

```text
NaN
+Infinity
-Infinity
```

Do not introduce engineering-range validation in this story. Valid ranges are metric-specific
business knowledge that has not yet been defined.

### Unit

`unit` is the source measurement unit.

Required behavior:

- trim leading/trailing whitespace;
- preserve case and Unicode;
- length: 1..24 characters after trimming;
- reject ASCII control characters (`U+0000..U+001F`, `U+007F`);
- otherwise do not invent a unit catalog or conversion model.

Valid examples include:

```text
°C
rpm
psi
%
m/s²
```

### Observation timestamp

`observed_at`:

- must be timezone-aware;
- must be normalized to UTC internally;
- must preserve the represented instant.

Do **not** reject timestamps because they are in the future or old. Sensor clock-skew and delayed
delivery policy are not defined yet and must not be invented in this domain story.

### Immutability

A telemetry sample represents a historical measurement fact. Its public identity/measurement
fields must not be mutable after construction.

## Architecture Constraints

Telemetry is a separate bounded context per ADR-002.

Telemetry domain code must not import:

```text
aeropulse.fleet.*
FastAPI
Pydantic transport schemas
SQLAlchemy
Redis
Kafka/broker clients
AWS SDKs
HTTP clients
```

Standard-library imports are sufficient for this story. Add **no new dependency**.

## Error Contract

Domain validation failures must use Telemetry-specific `ValueError` subclasses with clear
names/messages, including equivalents of:

```text
InvalidTelemetryMetric
InvalidTelemetryValue
InvalidTelemetryUnit
InvalidTelemetryTimestamp
```

Exact internal module placement is an implementation choice.

## Acceptance Criteria

### AC1 — Valid sample

Given a UUID sample ID, UUID Equipment ID, metric `" Oil_Temperature "`, finite value `87.5`,
unit `" °C "`, and a timezone-aware timestamp,
when a sample is created,
then:

- metric is exposed as `oil_temperature`;
- value remains `87.5`;
- unit is exposed as `°C`;
- `observed_at` is UTC;
- the same instant is preserved;
- IDs are unchanged.

### AC2 — Metric validation

Invalid metric inputs are rejected, including:

```text
""
"   "
"1temperature"
"oil-temperature"
"oil temperature"
"oil.temperature"
"oil/temperature"
<more than 64 characters>
```

### AC3 — Unit validation

Unit values are trimmed and case/Unicode are preserved.

Empty units, units longer than 24 characters, and units containing ASCII control characters are
rejected.

### AC4 — Non-finite values

`NaN`, positive infinity, and negative infinity are rejected.

### AC5 — Timezone requirement

A naive `datetime` is rejected.

A non-UTC aware `datetime` is accepted and normalized to UTC without changing the instant.

### AC6 — No invented freshness policy

A timezone-aware timestamp in the future is accepted by this domain model.

This acceptance criterion exists specifically to prevent implementation agents from inventing
clock-skew/freshness requirements.

### AC7 — Architecture boundary

Telemetry domain modules contain no imports from Fleet, FastAPI, SQLAlchemy, Redis, brokers,
cloud SDKs, or HTTP clients.

### AC8 — Scope discipline

The story introduces:

- no migration;
- no persistence repository;
- no FastAPI route/schema;
- no batch model;
- no idempotency implementation;
- no metric catalog;
- no unit-conversion framework;
- no new dependency.

## Security / Data Integrity

- bound identifier/unit lengths to avoid accepting arbitrarily large domain strings;
- reject control characters in units;
- reject non-finite numeric values before later serialization/persistence;
- do not log measurement payloads as part of validation;
- do not treat domain validation as a substitute for future HTTP request-size limits.

## Non-goals

Explicitly out of scope:

- PostgreSQL/Timescale persistence;
- migrations;
- HTTP ingestion;
- batch ingestion;
- duplicate/idempotency handling;
- Equipment existence lookup;
- Aircraft lifecycle checks;
- telemetry retention;
- unit conversion;
- metric-specific min/max ranges;
- sensor registry;
- Kafka/Redpanda;
- outbox/events;
- health scoring;
- anomaly detection;
- RUL/degradation logic.

## Validation

Required locally:

```text
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
uv lock --check
```

Add focused unit tests under the Telemetry domain test area for every acceptance criterion.

Do not weaken existing quality gates.

## Open Questions

None. Any newly discovered requirement must be proposed as a spec change or follow-up ticket,
not inferred during implementation.
