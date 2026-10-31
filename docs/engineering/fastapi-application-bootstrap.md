# AeroPulse — FastAPI Application Bootstrap

**Ticket:** S0-006 — FastAPI application with `/health` and `/ready`
**Status:** Accepted for Sprint 0

## 1. Purpose

S0-006 introduces the first AeroPulse runtime application.

The ticket establishes:

- FastAPI as the HTTP framework;
- validated runtime configuration;
- an application factory;
- lifespan-based startup/shutdown state;
- operational liveness and readiness endpoints;
- HTTP-level tests using FastAPI's test client.

It deliberately does **not** introduce PostgreSQL, Redis, Kafka, authentication, business APIs,
Docker, or cloud infrastructure.

## 2. Runtime Dependencies

AeroPulse now directly depends on:

```text
FastAPI
Pydantic
pydantic-settings
Uvicorn
```

`httpx` is a development dependency because FastAPI's `TestClient` uses HTTPX.

Dependencies are declared directly when AeroPulse imports or invokes them. Transitive dependencies
are not treated as implicit project APIs.

## 3. Application Factory

The application is created with:

```python
create_app(settings: Settings | None = None) -> FastAPI
```

rather than a module-level global application instance.

Reasons:

- settings can be injected in tests;
- importing a module does not start application resources;
- future startup resources can remain inside lifespan;
- different deployment/test configurations can construct isolated applications.

The development server is started with Uvicorn's factory mode:

```bash
uv run --locked uvicorn aeropulse.api.app:create_app --factory
```

## 4. Configuration

Configuration is owned by:

```text
src/aeropulse/settings.py
```

Environment variables use the prefix:

```text
AEROPULSE_
```

Current settings:

```text
AEROPULSE_APP_NAME
AEROPULSE_ENVIRONMENT
AEROPULSE_DEBUG
```

Supported environments:

```text
local
test
staging
production
```

A local `.env` file may be used for development.

`.env.example` contains safe examples only.

Real secrets must never be committed.

## 5. Fail-Fast Configuration

The settings model rejects:

```text
environment=production
debug=true
```

This is an explicit security invariant.

Configuration errors should prevent application startup instead of silently running with an unsafe
configuration.

Future mandatory settings should follow the same fail-fast principle.

## 6. Lifespan

AeroPulse uses FastAPI's `lifespan` async context manager.

It does **not** use the deprecated `@app.on_event("startup")` or
`@app.on_event("shutdown")` APIs.

Current lifecycle:

```text
application created
      |
      v
ready = false
      |
lifespan startup
      |
      v
ready = true
      |
serve requests
      |
lifespan shutdown
      |
      v
ready = false
```

Future resources such as database pools should be initialized before readiness becomes true and
released during lifespan shutdown.

## 7. Liveness vs Readiness

These endpoints have intentionally different semantics.

### `GET /health`

Purpose:

```text
Is the process alive enough to serve an HTTP response?
```

Response:

```json
{"status": "ok"}
```

Status:

```text
200
```

The liveness endpoint must remain shallow.

It must **not** become dependent on:

- PostgreSQL;
- Redis;
- Kafka;
- an external MRO API;
- ML model availability.

Otherwise an infrastructure outage could cause an orchestrator to repeatedly restart a healthy
application process.

### `GET /ready`

Purpose:

```text
Is this application instance ready to receive production traffic?
```

Before successful lifespan startup:

```text
503
{"status": "not_ready"}
```

During a successfully started lifespan:

```text
200
{"status": "ready"}
```

Future critical startup dependencies can contribute to readiness.

They must not automatically be copied into liveness.

## 8. Probe Caching

Both operational endpoints return:

```http
Cache-Control: no-store
```

Health/readiness responses are current operational state and must not be served from an intermediary
cache.

## 9. OpenAPI

`/health` and `/ready` are excluded from the generated OpenAPI schema.

They are infrastructure/operations endpoints rather than the versioned business API.

Future business endpoints will live under:

```text
/api/v1/...
```

as defined by the repository architecture.

## 10. Why No Database Readiness Check Yet?

S0-006 has no database.

Adding a fake PostgreSQL check would create an abstraction without a dependency.

S0-007 will introduce local dependencies. The readiness design can then be extended based on real
startup requirements.

This follows YAGNI.

## 11. Why No Custom Error Framework Yet?

The only non-2xx result in this ticket is a readiness `503` with a simple stable operational payload.

Creating a generic application-wide error hierarchy before the first business error exists would be
premature abstraction.

Business API error conventions should be introduced with the first business use case.

## 12. Testing Strategy

S0-006 creates meaningful HTTP integration tests under:

```text
tests/integration/api/
```

The tests verify:

- `/health` returns 200 even when lifespan has not started;
- `/ready` returns 503 before startup;
- `/ready` returns 200 while lifespan is active;
- readiness resets on shutdown;
- operational endpoints are excluded from OpenAPI;
- application settings are injectable;
- settings can be loaded from environment variables;
- unsafe production debug configuration is rejected.

FastAPI's `TestClient` must be used as a context manager when testing lifespan behavior.

## 13. Edge Cases Considered

### Application created but startup not completed

Expected:

```text
/health -> 200
/ready  -> 503
```

### Application successfully started

Expected:

```text
/health -> 200
/ready  -> 200
```

### Application shutting down

Readiness state returns to false.

### Invalid environment value

Pydantic settings validation fails at construction/startup.

### Production debug accidentally enabled

Settings validation fails.

### Local `.env` does not exist

Defaults/environment variables still work.

## 14. Risks and Mitigations

### Liveness checks too many dependencies

**Risk:** restart storms during infrastructure incidents.

**Mitigation:** `/health` performs no external dependency checks.

### Readiness always returns 200

**Risk:** load balancer sends traffic before initialization finishes.

**Mitigation:** readiness is tied to lifespan state.

### Global application state becomes untestable

**Risk:** tests leak configuration/resources into one another.

**Mitigation:** use `create_app()` and injectable settings.

### Configuration typo or unsafe production mode

**Risk:** application launches with incorrect behavior.

**Mitigation:** typed Pydantic settings and explicit production-debug invariant.

### Framework code leaks into domain

**Risk:** business logic becomes coupled to FastAPI.

**Mitigation:** this ticket creates only the API/application bootstrap; no domain package imports
FastAPI.

### Premature dependency checks

**Risk:** fake abstractions are created for PostgreSQL/Redis before those services exist.

**Mitigation:** defer dependency readiness integration to S0-007.

## 15. Local Run

After regenerating the dependency lock:

```bash
uv lock
uv sync --locked
```

Start the API:

```bash
uv run --locked uvicorn aeropulse.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Validate:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
```

Expected while running normally:

```text
/health -> 200
/ready  -> 200
```

## 16. Definition of Done

Using the target Python/uv environment, S0-006 is complete when:

```bash
uv lock
uv sync --locked --group dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

all pass, CI passes, and manual `/health` and `/ready` smoke checks return 200 after startup.
