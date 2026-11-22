# AeroPulse Architecture Decision Records

Architecture Decision Records (ADRs) capture significant technical decisions whose rationale
should remain understandable after the implementation context is gone.

ADRs live only in:

```text
docs/adr/
```

## When an ADR is required

Create or update an ADR when a decision is significant, cross-cutting, costly to reverse, or
likely to be repeatedly questioned. Examples include:

- introducing a new bounded context or cross-context dependency rule;
- selecting a database technology or persistence pattern;
- introducing a broker or asynchronous delivery guarantee;
- choosing an authentication/authorization mechanism;
- creating a new deployable service;
- changing a public API/event compatibility strategy;
- changing deployment/cloud architecture;
- adopting a repository-wide engineering process that changes how features are delivered.

Do not create ADRs for routine implementation details that can be understood from code/tests.

## Status lifecycle

```text
Proposed -> Accepted -> Superseded
               |
               +-> Deprecated
```

Rejected decisions may remain as `Rejected` when the rationale is useful.

Accepted ADRs are not edited to rewrite history. If the decision materially changes, create a
new ADR and mark the previous record Superseded.

## Naming

```text
ADR-001-short-decision-title.md
ADR-002-short-decision-title.md
```

## Index

| ADR | Status | Decision |
|---|---|---|
| [ADR-001](ADR-001-spec-driven-development.md) | Accepted | Adopt spec-driven development for scoped feature delivery |
| [ADR-002](ADR-002-telemetry-bounded-context.md) | Accepted | Model Telemetry as a separate bounded context inside the modular monolith |
