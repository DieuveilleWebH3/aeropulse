# AeroPulse — Repository Architecture & Structure

**Document status:** Accepted for Sprint 0
**Ticket:** S0-001 — Define repository architecture and engineering guardrails
**Scope:** Repository organization, dependency rules, package boundaries, naming, testing layout, documentation layout, infrastructure layout, and agent-facing conventions.
**Out of scope:** Runtime implementation, FastAPI bootstrap, database models, Kafka, ML, Airflow, Terraform resources, production deployment.

---

## 1. Purpose

This document is the source of truth for the physical structure of the AeroPulse repository.

Its goals are to:

1. give developers and coding agents a predictable map of the codebase;
2. keep domain logic independent from frameworks and infrastructure;
3. make architectural boundaries explicit before feature implementation;
4. support incremental delivery without prematurely creating unnecessary services;
5. make testing, CI/CD, documentation, observability, and deployment concerns first-class;
6. reduce accidental coupling between bounded contexts;
7. provide enough structure for future growth without violating KISS or YAGNI.

This document defines the **target structure**. Directories must be created only when a ticket requires them.

---

## 2. Engineering Principles

### 2.1 KISS — Keep It Simple

Prefer the smallest design that satisfies the current use case and acceptance criteria.

Examples:

- start with a modular FastAPI application instead of multiple deployable microservices;
- introduce Kafka only when asynchronous/event-driven processing is required by a ticket;
- introduce Redis only for a demonstrated caching, coordination, or rate-limiting need;
- avoid a generic framework around business rules before at least two concrete use cases justify it.

### 2.2 YAGNI — You Aren't Gonna Need It

Do not add infrastructure or abstractions only because they may be useful later.

Not part of the initial foundation unless a later ticket explicitly requires them:

- Kubernetes;
- service mesh;
- multi-region active-active deployment;
- CQRS as a platform-wide pattern;
- Event Sourcing;
- GraphQL;
- multiple databases for the same type of operational data;
- generic plugin systems;
- complex internal SDKs.

### 2.3 DRY — Don't Repeat Yourself

Avoid duplication of **knowledge**, especially:

- business rules;
- validation semantics;
- error codes;
- event schemas;
- authorization rules;
- configuration conventions.

Do not create abstractions merely to eliminate small syntactic duplication.

### 2.4 SOLID

The codebase should follow SOLID pragmatically:

- **S — Single Responsibility:** each module/class/function has one primary reason to change.
- **O — Open/Closed:** stable contracts allow new implementations without rewriting orchestration logic.
- **L — Liskov Substitution:** adapters that implement the same port preserve the same behavioral contract.
- **I — Interface Segregation:** small focused ports are preferred over large generic interfaces.
- **D — Dependency Inversion:** business/application logic depends on abstractions; infrastructure implements them.

---

## 3. Architectural Style

AeroPulse starts as a **modular monolith with independently executable workers where operational characteristics justify them**.

The initial architectural direction is:

```text
Presentation / Transport
        |
        v
Application
        |
        v
Domain
        ^
        |
Infrastructure Adapters
```

The domain layer must not depend on FastAPI, SQLAlchemy, Kafka, Redis, AWS SDKs, HTTP clients, or other delivery/infrastructure frameworks.

### 3.1 Why not microservices initially?

Microservices would introduce distributed-system costs before the domain boundaries and scaling needs are proven:

- network failures;
- service discovery;
- versioned inter-service contracts;
- more CI/CD pipelines;
- distributed tracing requirements;
- deployment coordination;
- higher local-development complexity.

A bounded context may become a separately deployable service later only when there is a measurable reason such as independent scaling, security isolation, ownership, reliability, or deployment cadence.

---

## 4. Target Repository Layout

```text
aeropulse/
|
|-- .github/
|   |-- agents/
|   |-- instructions/
|   |-- prompts/
|   |-- workflows/
|   |-- ISSUE_TEMPLATE/
|   |-- PULL_REQUEST_TEMPLATE.md
|   `-- copilot-instructions.md
|
|-- apps/
|   |-- api/
|   |-- telemetry_worker/
|   `-- phm_worker/
|
|-- src/
|   `-- aeropulse/
|       |-- api/
|       |-- fleet/
|       |-- telemetry/
|       |-- health/
|       |-- anomalies/
|       |-- maintenance/
|       |-- identity/
|       |-- audit/
|       `-- shared/
|
|-- tests/
|   |-- unit/
|   |-- integration/
|   |-- contract/
|   `-- e2e/
|
|-- migrations/
|
|-- infrastructure/
|   |-- docker/
|   `-- terraform/
|
|-- scripts/
|
|-- docs/
|   |-- architecture/
|   |   |-- decisions/
|   |   `-- repository-structure.md
|   |-- engineering/
|   |-- api/
|   |-- events/
|   `-- runbooks/
|
|-- .env.example
|-- .gitignore
|-- .python-version
|-- .pre-commit-config.yaml
|-- docker-compose.yml
|-- pyproject.toml
|-- uv.lock
|-- README.md
|-- CONTRIBUTING.md
`-- LICENSE
```

This is a **target**, not a command to create every directory immediately.

---

## 5. What Exists Now vs. What Is Created Later

### Create in S0-001

```text
docs/
`-- architecture/
    `-- repository-structure.md
```

### Create in subsequent Sprint 0 tickets

```text
.github/
src/
tests/
apps/
pyproject.toml
.python-version
uv.lock
.pre-commit-config.yaml
```

### Create only when required by a concrete feature

```text
migrations/
infrastructure/docker/
infrastructure/terraform/
docs/events/
docs/runbooks/
telemetry_worker/
phm_worker/
```

This rule prevents empty scaffolding from becoming accidental architecture.

---

## 6. Python Source Layout

Application source code uses the `src` layout:

```text
src/
`-- aeropulse/
```

Reasons:

- prevents accidental imports from the repository root;
- makes packaging behavior closer to installed-production behavior;
- keeps source code separate from tests, scripts, docs, and infrastructure.

The root Python package is:

```text
aeropulse
```

---

## 7. Bounded Context Layout

A bounded context is created only when its first user story is implemented.

Typical structure:

```text
src/aeropulse/<context>/
|-- domain/
|-- application/
|-- infrastructure/
`-- presentation/
```

Example:

```text
src/aeropulse/fleet/
|-- domain/
|   |-- entities.py
|   |-- value_objects.py
|   |-- errors.py
|   `-- ports.py
|
|-- application/
|   |-- commands.py
|   |-- queries.py
|   `-- services.py
|
|-- infrastructure/
|   `-- persistence/
|
`-- presentation/
    `-- http/
```

Do not create every file above automatically. Split files only when their responsibilities warrant separation.

---

## 8. Layer Responsibilities

### 8.1 Domain

Contains business concepts and invariants.

Allowed:

- entities;
- value objects;
- domain services;
- domain errors;
- domain events;
- protocol/port definitions when they are domain-owned.

Forbidden dependencies:

- FastAPI;
- SQLAlchemy ORM;
- Pydantic transport models;
- Redis client;
- Kafka client;
- boto3;
- HTTPX;
- framework-specific dependency injection.

The domain should remain testable with plain Python.

### 8.2 Application

Coordinates use cases.

Responsibilities:

- commands and queries;
- transaction/use-case orchestration;
- authorization decisions when use-case-specific;
- invoking domain behavior;
- invoking ports;
- mapping domain failures to application failures.

It must not contain HTTP-specific response construction or database-specific queries.

### 8.3 Infrastructure

Implements technical adapters.

Examples:

- SQLAlchemy repositories;
- PostgreSQL persistence;
- Kafka publisher/consumer adapters;
- Redis adapters;
- S3 storage adapters;
- HTTP clients to external MRO systems.

Infrastructure may depend on application/domain contracts.

Domain/application must not depend on concrete infrastructure adapters.

### 8.4 Presentation

Handles transport concerns.

Examples:

- FastAPI routers;
- request/response schemas;
- dependency wiring;
- HTTP status-code mapping;
- authentication extraction.

Routers must remain thin.

A route should generally:

1. parse transport input;
2. invoke an application use case;
3. map the result to an API response.

A route must not implement business workflows directly.

---

## 9. Cross-Context Dependency Rules

Bounded contexts must not freely import each other's internal modules.

Forbidden example:

```python
from aeropulse.fleet.infrastructure.models import AircraftRow
```

from another bounded context.

Prefer:

- application-level contracts;
- stable public interfaces;
- domain identifiers/value objects where appropriate;
- domain/application events for asynchronous communication.

Direct database-table coupling across contexts is discouraged.

If a cross-context dependency becomes necessary, document the dependency and evaluate whether an ADR is required.

---

## 10. Shared Package Policy

`src/aeropulse/shared/` is deliberately restricted.

It may contain genuinely cross-cutting technical primitives such as:

- common typing utilities;
- correlation-ID primitives;
- base time/clock abstraction;
- generic result/error primitives if they are truly common.

It must **not** become a dumping ground for:

- business rules;
- generic `utils.py`;
- context-specific DTOs;
- context-specific repositories;
- unrelated helper functions.

Before moving code to `shared`, ask:

> Is this concept truly owned by no single bounded context and required by multiple contexts?

If the answer is unclear, keep it local.

---

## 11. Executable Applications

`apps/` contains executable entry points, not business logic.

Target applications:

```text
apps/api/
apps/telemetry_worker/
apps/phm_worker/
```

### API

Starts the FastAPI application.

### Telemetry worker

Created only when Sprint 3 introduces asynchronous telemetry processing.

### PHM worker

Created only when health/anomaly processing needs an independently executable workload.

Business logic remains in `src/aeropulse/...`.

---

## 12. Testing Structure

```text
tests/
|-- unit/
|-- integration/
|-- contract/
`-- e2e/
```

### Unit tests

Test domain/application behavior in isolation.

Characteristics:

- fast;
- deterministic;
- no network;
- no real database;
- no Docker requirement.

### Integration tests

Test boundaries against real infrastructure components where useful.

Examples:

- SQLAlchemy repository against PostgreSQL;
- Redis adapter;
- Kafka adapter.

Prefer disposable test infrastructure over mocks when the integration contract itself is the subject of the test.

### Contract tests

Validate integration contracts.

Examples:

- MRO API request/response contract;
- event schema compatibility.

### E2E tests

Validate a small number of critical business flows.

Example:

```text
telemetry
-> anomaly
-> recommendation
-> approved maintenance action
```

E2E tests should not replace unit/integration tests.

---

## 13. Testing Principles

Tests should validate behavior, invariants, contracts, and failure modes rather than private implementation details.

Avoid:

- asserting internal method call counts without a behavioral reason;
- snapshotting large unstable payloads;
- one test per trivial getter;
- chasing coverage percentages by adding low-value tests.

Critical paths should cover:

- happy path;
- validation failure;
- duplicate/idempotent input;
- concurrency conflict where relevant;
- dependency timeout/failure;
- authorization failure;
- state-transition violation.

---

## 14. Documentation Structure

```text
docs/
|-- architecture/
|   |-- decisions/
|   `-- repository-structure.md
|-- engineering/
|-- api/
|-- events/
`-- runbooks/
```

### `docs/architecture/`

System design, C4 documentation, architectural boundaries.

### `docs/architecture/decisions/`

Architecture Decision Records.

An ADR is justified for decisions that are:

- difficult or expensive to reverse;
- cross-cutting;
- likely to be questioned later;
- important to reliability, security, data integrity, or deployment.

### `docs/engineering/`

Developer workflow, testing strategy, Copilot/agent strategy, release process.

### `docs/api/`

API conventions and non-generated API documentation.

OpenAPI remains the executable HTTP contract.

### `docs/events/`

Event naming, envelopes, schemas, compatibility rules. Create when event-driven processing begins.

### `docs/runbooks/`

Operational procedures. Create when there are real operational components to run.

---

## 15. GitHub and Coding-Agent Structure

Target structure:

```text
.github/
|-- agents/
|-- instructions/
|-- prompts/
|-- workflows/
|-- ISSUE_TEMPLATE/
|-- PULL_REQUEST_TEMPLATE.md
`-- copilot-instructions.md
```

Responsibilities:

- `copilot-instructions.md`: repository-wide rules that apply to agent work;
- `instructions/*.instructions.md`: path-specific rules;
- `agents/`: specialized agent profiles;
- `prompts/`: reusable task prompts;
- `workflows/`: deterministic CI/CD automation.

Important principle:

> AI agents may design or maintain deterministic automation, but deterministic automation must not be replaced by AI agents.

For example, an agent may maintain `ci.yml`; CI itself must run from GitHub Actions.

---

## 16. Configuration

Runtime configuration must be externalized.

Rules:

- no secrets committed to Git;
- `.env.example` contains names and safe examples only;
- production secrets come from the deployment platform/secret manager;
- configuration is validated at startup;
- environment-specific behavior is explicit.

Do not silently provide insecure production defaults.

---

## 17. Dependency Management

AeroPulse uses **uv** as the Python package and environment manager.

Target files:

```text
pyproject.toml
uv.lock
.python-version
```

Rules:

- `pyproject.toml` declares direct dependencies and tool configuration;
- `uv.lock` is committed;
- CI installs from the lock file;
- transitive dependencies are not manually added unless directly required;
- dependency upgrades must pass tests and security checks.

The exact commands are defined in the Sprint 0 Python bootstrap ticket rather than in this architecture document, because they depend on the chosen Python/tool versions.

---

## 18. Database and Migration Policy

PostgreSQL is the initial operational relational database.

Database migrations will use Alembic when the first persistent domain model is introduced.

Rules:

- schema changes are versioned;
- destructive migrations require explicit review;
- application and migration compatibility must be considered for deployment;
- business uniqueness invariants should be protected with database constraints where possible;
- application-side `exists()` checks are not sufficient protection against race conditions.

---

## 19. API Conventions

API implementation is added in a later ticket.

Target conventions:

```text
/api/v1/...
/health
/ready
```

Rules:

- transport schemas are separate from domain entities;
- errors use a stable structured format;
- correlation identifiers are propagated;
- pagination is mandatory for unbounded collection endpoints;
- endpoint handlers stay thin;
- API versioning is explicit for public/business APIs.

Health and readiness endpoints are operational endpoints and are not placed under `/api/v1`.

---

## 20. Event-Driven Conventions

Event infrastructure is not introduced until the corresponding sprint.

When introduced:

- events are immutable facts;
- event names use past tense;
- schemas are versioned;
- consumers are designed for at-least-once delivery;
- idempotency is explicit;
- business identifiers and event identifiers are distinct;
- correlation/causation metadata is propagated;
- retry and DLQ behavior is bounded and observable.

Example future event name:

```text
telemetry.received.v1
```

Do not build an event framework in Sprint 0.

---

## 21. Naming Conventions

### Python

- packages/modules: `snake_case`
- functions: `snake_case`
- variables: `snake_case`
- classes: `PascalCase`
- constants: `UPPER_SNAKE_CASE`
- private implementation detail: leading `_` when appropriate

### Business names

Prefer domain language over technical aliases.

Good:

```text
MaintenanceRecommendation
AircraftRegistration
TelemetrySample
```

Avoid:

```text
DataManager
Helper
GenericService
Processor2
```

### Tests

Use behavioral names.

Example:

```python
def test_register_aircraft_rejects_duplicate_registration():
    ...
```

---

## 22. Import and Dependency Guardrails

High-level rule:

```text
domain <- application <- presentation
   ^          ^
   |          |
   +----- infrastructure
```

More precisely:

- domain imports Python standard library and explicitly approved pure-Python domain dependencies only;
- application may import domain;
- infrastructure may import domain/application contracts;
- presentation may import application and transport-specific dependencies;
- no domain import from infrastructure/presentation;
- no circular dependencies between bounded contexts.

Architectural tests may later enforce these rules automatically.

---

## 23. Error Handling

Errors should be represented at the layer that owns their meaning.

Examples:

- domain: invalid state transition;
- application: requested resource unavailable for a use case;
- infrastructure: database/network failure;
- presentation: mapping errors to HTTP responses.

Do not expose raw SQL, stack traces, secrets, or internal dependency errors to API clients.

---

## 24. Observability by Design

Observability is not fully implemented in S0-001, but code should be written so that it can later support:

- structured logging;
- correlation IDs;
- metrics;
- distributed tracing.

Do not use `print()` for application logging.

Instrumentation must not leak secrets or sensitive payloads.

---

## 25. Security by Design

Every future ticket must consider:

- input validation;
- authentication impact;
- authorization impact;
- secret handling;
- logging exposure;
- dependency vulnerabilities;
- injection risks;
- SSRF when calling external systems;
- resource exhaustion;
- replay/duplicate processing;
- concurrency/race conditions.

Security review is part of Definition of Done, not a final project phase.

---

## 26. Performance Policy

Do not optimize without evidence.

Required sequence:

```text
measure
-> identify bottleneck
-> establish baseline
-> optimize
-> benchmark again
```

Avoid introducing caching, concurrency, batching, or distributed systems solely for perceived performance.

Correctness and observability come before optimization.

---

## 27. Files and Patterns to Avoid

Avoid generic catch-all files such as:

```text
utils.py
helpers.py
common.py
base_service.py
manager.py
```

unless the contained responsibility is clearly defined.

Avoid deep inheritance trees.

Prefer composition and explicit ports/adapters.

Avoid large framework-specific base classes inherited by all contexts.

---

## 28. Pull Request Boundaries

A pull request should ideally represent one coherent ticket or narrowly related set of changes.

A PR should not casually mix:

- feature implementation;
- unrelated refactoring;
- dependency upgrades;
- formatting of unrelated files;
- infrastructure redesign.

Small PRs improve human review and coding-agent reliability.

---

## 29. Definition of Done Impact

A ticket changing production code is not done until the applicable checks pass:

- acceptance criteria;
- unit tests;
- integration/contract tests where relevant;
- lint;
- formatting;
- static typing;
- security checks;
- documentation changes;
- migration review where relevant;
- observability impact considered;
- backward compatibility considered.

Exact commands are established by later Sprint 0 tooling tickets.

---

## 30. Architectural Change Process

If implementation reveals that this structure is insufficient:

1. identify the concrete problem;
2. document evidence/constraints;
3. propose the smallest viable change;
4. assess impact on dependency rules;
5. create an ADR when the decision is significant;
6. update this document if repository-level structure changes.

This document must evolve based on real requirements, not speculative architecture.

---

## 31. Initial Sprint 0 Sequence

The expected foundation sequence is:

```text
S0-001 Repository architecture and guardrails
S0-002 Copilot agent governance and repository instructions
S0-003 Python + uv project bootstrap
S0-004 Code quality and test toolchain
S0-005 Minimal GitHub Actions CI
S0-006 FastAPI application with /health and /ready
S0-007 Local dependencies and Docker Compose
```

Each ticket must be independently reviewable and leave the repository in a valid state.

---

## 32. Decision Summary

For the initial AeroPulse implementation:

- modular monolith first;
- bounded contexts with clean internal layering;
- `src/` Python layout;
- thin FastAPI presentation layer;
- domain independent from frameworks;
- workers only when asynchronous workloads justify them;
- one repository;
- uv for Python dependency management;
- PostgreSQL as the first operational relational store;
- tests separated by purpose;
- deterministic CI/CD in GitHub Actions;
- coding agents governed by repository instructions;
- incremental architecture under KISS/YAGNI.

The guiding rule is:

> Build the smallest reliable vertical slice that satisfies the current ticket, while preserving clear boundaries for the next one.
