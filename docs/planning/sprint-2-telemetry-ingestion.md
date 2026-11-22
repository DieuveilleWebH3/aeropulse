# Sprint 2 — Telemetry Ingestion Foundation

## Sprint Goal

Move AeroPulse from Fleet inventory into PHM data capture by establishing a secure,
deterministic Telemetry bounded context and a minimal end-to-end ingestion/query foundation.

The sprint deliberately does **not** introduce anomaly detection, ML/RUL, Kafka, or a separate
telemetry service.

## Engineering Experiment

Sprint 2 also validates the repository's Spec-Driven Development and multi-agent governance.

S2-001 is the controlled experiment:

```text
Approved spec
   -> Spec Delivery Orchestrator
   -> Architect gate
   -> Backend implementation
   -> Test Engineer independent pass
   -> Security & Quality review
   -> deterministic CI
   -> human review
```

Success is measured by spec adherence and review quality, not by how many agents are invoked.

## Backlog

### S2-000 — Spec-Driven Development & Agent Orchestration

Add:

- `docs/adr/` registry and initial ADRs;
- `docs/specs/` workflow;
- coordination-only orchestrator;
- spec prompts/instructions;
- Sprint 2 plan and first approved specification.

No production behavior.

### S2-001 — Telemetry Sample Domain Model

Implement the approved spec:

`docs/specs/S2-001-telemetry-sample-domain.md`

Pure domain/value-object work and unit tests only.

No persistence/API/dependency changes.

### S2-002 — Telemetry Persistence & Idempotent Storage

Persist validated samples and define duplicate/retry semantics.

Before implementation, decide/document any significant persistence/idempotency strategy with
an ADR. Do not assume TimescaleDB or a broker without evidence.

Expected concerns:

- database constraints;
- Equipment reference validation at the application boundary;
- idempotent sample identity;
- deterministic timestamp/value storage;
- migration `0006` or later.

### S2-003 — Telemetry Ingestion Application Use Case

Introduce the application command/handler and transaction semantics around Equipment validation
and telemetry persistence.

Keep transport concerns out of the domain/application contract.

### S2-004 — Telemetry HTTP Ingestion API

Expose the minimal single-sample ingestion endpoint with stable HTTP errors and OpenAPI
documentation.

Batch ingestion remains out of scope unless a measured/current requirement appears.

### S2-005 — Telemetry Read / Time-Window Query API

Retrieve Equipment telemetry by bounded time window and deterministic ordering.

Define pagination/limits explicitly to prevent unbounded queries.

### S2-006 — Ingestion Observability & Resource Guardrails

Add only the operational signals/limits justified by the ingestion path:

- structured outcome/error logging without sensitive payload dumps;
- bounded query/request behavior;
- actionable metrics if the current observability stack supports them.

Do not add a new observability platform solely for this ticket.

### S2-007 — Telemetry Integration & E2E Validation

Prove:

```text
register Aircraft
  -> register Equipment
  -> ingest telemetry
  -> retrieve telemetry
  -> duplicate/retry behavior
  -> invalid sample behavior
```

### S2-008 — Sprint 2 Release

Prepare `v0.2.0` only after Sprint 2 acceptance criteria and full quality gates are green.

## Sprint-wide Non-goals

- Kafka/Redpanda;
- microservices;
- TimescaleDB unless a later ADR/ticket demonstrates a current need;
- batch ingestion by default;
- streaming analytics;
- anomaly detection;
- ML training/inference;
- RUL estimation;
- maintenance recommendation workflows;
- authentication/RBAC unless separately prioritized.

## Definition of Done

Every implementation ticket must satisfy its approved specification and applicable ADRs, with:

```text
uv lock --check
uv run --locked --group migration alembic check   # when persistence metadata is affected
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

Agent-generated work still requires human review.
