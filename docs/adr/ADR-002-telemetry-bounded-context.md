# ADR-002 — Model Telemetry as a separate bounded context inside the modular monolith

- Status: Accepted
- Date: 2026-11-22
- Deciders: AeroPulse maintainers
- Technical area: Domain architecture / Telemetry

## Context

Sprint 1 established the `fleet` bounded context for Aircraft and Equipment identity/lifecycle.

Sprint 2 introduces time-series telemetry. Telemetry has different rules and future evolution:
ingestion, idempotency, time-window queries, high write volume, data quality, health-analysis
consumers, and potentially different persistence characteristics.

Putting telemetry business rules directly inside `fleet` would make Fleet own both asset
identity and measurement-stream concerns. Creating a separate service now would introduce
deployment/distributed-system complexity before it is needed.

## Decision Drivers

- keep Fleet focused on asset identity and lifecycle;
- allow telemetry rules to evolve independently;
- preserve the current modular-monolith deployment;
- avoid speculative microservices/brokers;
- prevent domain-level coupling to Fleet infrastructure;
- keep future extraction possible without designing for it prematurely.

## Options Considered

### Option A — Put Telemetry inside `fleet`

Simple initially, but mixes asset lifecycle and time-series measurement responsibilities.

### Option B — Separate `telemetry` bounded context inside the modular monolith

Keeps domain boundaries while retaining one application/deployment.

### Option C — Separate Telemetry microservice now

Maximizes deployment independence but introduces network contracts, operational overhead,
distributed failure modes, and deployment complexity before a concrete requirement exists.

## Decision

Select **Option B**.

Sprint 2 telemetry code belongs under:

```text
src/aeropulse/telemetry/
```

with the same inward dependency direction used elsewhere:

```text
Presentation -> Application -> Domain
Infrastructure -> Application/Domain contracts
```

Telemetry domain code must not import Fleet aggregates, Fleet repositories, SQLAlchemy, FastAPI,
Redis, brokers, or cloud SDKs.

Telemetry may carry an `equipment_id: UUID` as an external identity reference. When a future
application use case must verify Equipment existence/state, that coordination must occur at the
application boundary through an explicit port/adaptor, not through a Telemetry-domain import of
Fleet infrastructure.

This ADR does **not** decide telemetry persistence technology, batch APIs, brokers, or event
delivery. Those decisions require their own concrete tickets/evidence.

## Consequences

### Positive

- clear ownership between asset lifecycle and measurement facts;
- telemetry can evolve without bloating Fleet;
- no new deployable service is introduced;
- domain remains framework-independent;
- future extraction remains possible if operational evidence later justifies it.

### Negative

- some use cases will require explicit cross-context coordination;
- duplicate identity representations such as Equipment UUID references must be handled carefully.

### Risks and mitigations

**Risk:** accidental direct imports from `fleet.infrastructure`.

**Mitigation:** repository instructions and architecture tests/review enforce bounded-context
dependency rules.

**Risk:** developers treat the context boundary as a reason to add messaging immediately.

**Mitigation:** this ADR explicitly keeps synchronous in-process coordination acceptable until
a real asynchronous requirement exists.

## Rejected / Deferred Alternatives

A separate telemetry service and message broker are deferred under YAGNI.

Telemetry persistence technology is deliberately not chosen by this ADR.

## Revisit Triggers

Reconsider deployment boundaries if measured requirements show:

- telemetry write/query load materially harms the shared application runtime;
- independent scaling/deployment becomes operationally necessary;
- fault isolation requirements cannot be met inside the modular monolith;
- organizational ownership requires a separately deployed service.
