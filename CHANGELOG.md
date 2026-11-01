# Changelog

All notable changes to AeroPulse are documented in this file.

AeroPulse follows semantic versioning. During the `0.x` series, the project is still under
active development and public APIs may evolve between minor releases.

## [0.1.0] - 2026-11-01

### Added

- Modular-monolith FastAPI application structure with clear presentation, application,
  domain, and infrastructure boundaries.
- PostgreSQL and Redis local runtime dependencies with application readiness checks.
- Async SQLAlchemy persistence and Alembic migration infrastructure.
- Aircraft registration with canonical registration validation and database uniqueness.
- Aircraft retrieval and deterministic offset-based fleet listing.
- Explicit Aircraft lifecycle with idempotent `ACTIVE -> RETIRED` transition and
  `retired_at` persistence.
- Equipment domain model linked to Aircraft.
- Fleet-wide physical Equipment identity based on `(part_number, serial_number)`.
- Equipment registration protected against concurrent Aircraft retirement.
- Equipment retrieval and per-Aircraft listing.
- Stable HTTP business-error envelopes for Aircraft and Equipment APIs.
- Swagger UI, ReDoc, and OpenAPI documentation with AeroPulse project metadata.
- Repository security policy, contribution guidelines, code of conduct, and MIT license.
- Unit, integration, contract, persistence, concurrency, and end-to-end validation.
- Sprint 1 E2E workflows covering complete Fleet lifecycle, physical Equipment identity,
  and representative public failure contracts.

### Engineering

- CPython 3.14 toolchain managed with `uv`.
- Ruff linting and formatting.
- Strict mypy type checking.
- Pytest with branch coverage and a project-wide coverage threshold of at least 90%.
- GitHub Actions CI with PostgreSQL and Redis services.
- Append-only Alembic migration history through revision `20261101_0005`.
- Explicit database integrity constraints for lifecycle, uniqueness, and referential
  integrity.
- Transaction-scoped FastAPI database sessions.
- Conditional persistence updates for retirement concurrency safety.

### API

Sprint 1 exposes:

- `POST /api/v1/aircraft`
- `GET /api/v1/aircraft`
- `GET /api/v1/aircraft/{aircraft_id}`
- `POST /api/v1/aircraft/{aircraft_id}/retire`
- `POST /api/v1/aircraft/{aircraft_id}/equipment`
- `GET /api/v1/equipment/{equipment_id}`
- `GET /api/v1/aircraft/{aircraft_id}/equipment`

Operational endpoints:

- `GET /health`
- `GET /ready`

Interactive documentation:

- `/docs` — Swagger UI
- `/redoc` — ReDoc
- `/openapi.json` — OpenAPI schema

### Scope and safety

AeroPulse `v0.1.0` is an engineering demonstrator built with synthetic/public engineering
data. It is not a certified airworthiness, flight-safety, or maintenance-decision system.

### Known limitations

- Authentication, authorization, and RBAC are not yet implemented.
- Telemetry ingestion is not yet implemented.
- Health scoring, anomaly detection, degradation analysis, and remaining-useful-life
  estimation are planned for later sprints.
- Maintenance recommendations, approval workflows, audit events, and external MRO/work-order
  integration are not yet implemented.
- Offset pagination is intentionally used for the initial Fleet API; cursor pagination may
  be introduced later if measured scale requires it.
