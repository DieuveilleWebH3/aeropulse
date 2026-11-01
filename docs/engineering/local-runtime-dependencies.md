# AeroPulse — Local Runtime Dependencies

**Ticket:** S0-007 — Local dependencies + Docker Compose
**Status:** Accepted for Sprint 0

## 1. Purpose

S0-007 introduces the first external runtime dependencies used by AeroPulse:

- PostgreSQL;
- Redis.

The ticket provides reproducible local services, bounded connectivity checks, lifecycle ownership,
dynamic readiness, and live CI validation.

It intentionally does not introduce:

- ORM entities;
- repositories;
- Alembic migrations;
- Redis caching behavior;
- Kafka;
- production infrastructure.

## 2. Versions

Local/CI service images:

```text
PostgreSQL 18.6
Redis 8.10.3
```

Python connectivity:

```text
SQLAlchemy 2.1.x
asyncpg 0.32.x
redis-py 8.1.x
```

Service image tags are pinned to patch releases for developer reproducibility.

Production deployment later requires its own image/digest and upgrade policy.

## 3. Why PostgreSQL and Redis Now?

PostgreSQL is the selected operational relational store from the repository architecture.

Redis is introduced as an available runtime dependency for later short-lived coordination/caching
needs, but S0-007 gives Redis **no business responsibility yet**.

This distinction matters:

> Installing a technology does not justify inventing a use case for it.

S0-007 uses both only to establish infrastructure lifecycle and readiness.

## 4. Docker Compose

Start services:

```bash
docker compose up -d
```

Inspect:

```bash
docker compose ps
```

Expected:

```text
postgres   healthy
redis      healthy
```

Follow logs:

```bash
docker compose logs -f postgres redis
```

Stop without deleting data:

```bash
docker compose down
```

Destroy local data:

```bash
docker compose down -v
```

`down -v` is destructive and should only be used when intentionally resetting the local environment.

## 5. Network Exposure

Compose binds database ports to loopback only:

```text
127.0.0.1:5432
127.0.0.1:6379
```

They are not bound to all host interfaces.

The Compose credentials are development-only values.

This Compose file is not a production deployment specification.

## 6. Persistent Volumes

PostgreSQL:

```text
postgres_data -> /var/lib/postgresql
```

PostgreSQL 18 changed the official Docker image volume root from the historical
`/var/lib/postgresql/data` location to `/var/lib/postgresql`. AeroPulse follows the PostgreSQL 18
image layout and must not revert to the pre-18 mount path.

Redis:

```text
redis_data
```

Redis AOF is enabled locally so restarts behave more like a persistent runtime rather than silently
discarding all state.

No AeroPulse business feature relies on Redis persistence at this stage.

## 7. Configuration

The application requires:

```text
AEROPULSE_DATABASE_URL
AEROPULSE_REDIS_URL
```

These are represented as `SecretStr` values in Pydantic Settings so ordinary object representations
do not expose credentials.

Connectivity checks use:

```text
AEROPULSE_DEPENDENCY_TIMEOUT_SECONDS
```

Default:

```text
1.0 second
```

Allowed range:

```text
> 0 and <= 10 seconds
```

Readiness must fail quickly instead of hanging an orchestrator probe.


## Settings Construction Boundary

`database_url` and `redis_url` intentionally remain required settings.

AeroPulse does not add insecure local defaults merely to make static typing accept `Settings()`.

Environment-driven construction goes through:

```python
load_settings()
```

which calls:

```python
Settings.model_validate({})
```

For `BaseSettings`, pydantic-settings still applies configured settings sources such as environment
variables and `.env` files when `model_validate()` is used.

This provides one explicit boundary between:

```text
environment / dotenv
        ↓
load_settings()
        ↓
validated Settings
```

and keeps ordinary explicit test construction type-safe through:

```python
Settings.model_validate({...})
```

## 8. Runtime Resource Ownership

The application composition root creates:

```text
ApplicationResources
├── PostgresResource
└── RedisResource
```

during FastAPI lifespan startup.

Client construction itself is lazy with respect to network connectivity.

On shutdown, AeroPulse closes:

- the Redis client;
- the SQLAlchemy async engine/pool.

Global connections are not created at Python import time.


## SQLAlchemy Async Installation

AeroPulse imports `sqlalchemy.ext.asyncio`, so SQLAlchemy must be installed with its asyncio extra:

```toml
sqlalchemy[asyncio]
```

SQLAlchemy 2.1 no longer installs `greenlet` by default. The `[asyncio]` extra declares the required
`greenlet` runtime dependency explicitly.

Do not install `greenlet` manually as an unrelated direct dependency; the dependency belongs to the
SQLAlchemy asyncio feature we use.

## 9. PostgreSQL Connectivity

SQLAlchemy's async engine is used as the connection-pool boundary.

asyncpg is the PostgreSQL driver.

Readiness executes:

```sql
SELECT 1
```

No ORM metadata, entity, table, or migration is created in this ticket.

The first persistence story will introduce domain persistence deliberately.

## 10. Redis Connectivity

The asyncio redis-py client owns Redis connections.

Readiness performs:

```text
PING
```

S0-007 does not introduce:

- cache keys;
- TTL policy;
- distributed locks;
- sessions;
- rate limiting.

Those capabilities require concrete later use cases.

## 11. Dynamic Readiness

Liveness remains:

```text
GET /health
```

and does not contact external services.

Readiness is:

```text
GET /ready
```

and checks PostgreSQL and Redis concurrently.

Behavior:

```text
PostgreSQL UP + Redis UP
    -> 200 ready

PostgreSQL DOWN
    -> 503 not_ready

Redis DOWN
    -> 503 not_ready

resources not initialized
    -> 503 not_ready
```

A dependency can fail after startup and readiness reflects that failure on the next probe.

## 12. Why Readiness Does Not Reveal Individual Dependency Status

The public probe returns only:

```json
{"status": "ready"}
```

or:

```json
{"status": "not_ready"}
```

It does not expose hostnames, database names, stack traces, or dependency topology.

Detailed dependency diagnostics belong in structured logs/metrics, which are introduced later.

## 13. Failure Handling

Expected connection failures are converted into an unavailable readiness result.

Examples:

- connection refused;
- SQLAlchemy connectivity failure;
- Redis connectivity failure;
- timeout.

Unexpected programming errors are not broadly swallowed.

This keeps operational failure tolerant without hiding code defects.

## 14. CI Integration

S0-007 adds PostgreSQL and Redis GitHub Actions service containers to the existing `quality` job.

CI sets:

```text
AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1
```

so the live infrastructure integration test executes against real services.

Local developers do not need Docker for every unit-test run: without that flag, the live service test
is skipped.

Unit tests still cover runtime resource aggregation and failure behavior without network access.

## 15. Manual End-to-End Validation

Create local config:

```bash
copy .env.example .env
```

On PowerShell:

```powershell
Copy-Item .env.example .env
```

Start dependencies:

```bash
docker compose up -d
docker compose ps
```

Enable the live integration test.

Command Prompt:

```cmd
set AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1
uv run --locked pytest tests/integration/infrastructure
```

PowerShell:

```powershell
$env:AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS = "1"
uv run --locked pytest tests/integration/infrastructure
```

Then start AeroPulse:

```bash
uv run --locked uvicorn aeropulse.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Check:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
```

Both should return 200.

Stop Redis:

```bash
docker compose stop redis
```

Expected:

```text
/health -> 200
/ready  -> 503
```

Restart:

```bash
docker compose start redis
```

Expected after Redis becomes healthy:

```text
/ready -> 200
```

Repeat the same experiment with PostgreSQL.

This is the primary demonstration that liveness and readiness have different operational semantics.

## 16. Risks and Mitigations

### Dependency outage triggers process restart

**Risk:** infrastructure failures amplify into restart storms.

**Mitigation:** liveness never checks PostgreSQL or Redis.

### Dependency outage after startup is not detected

**Risk:** load balancer sends traffic to an unusable instance.

**Mitigation:** readiness checks dependencies dynamically on each probe.

### Probe hangs

**Risk:** readiness itself consumes workers/connections indefinitely.

**Mitigation:** database/Redis clients use bounded connection/socket timeouts.

### Password appears in logs/repr

**Risk:** credential leakage.

**Mitigation:** connection URLs are `SecretStr` and readiness logs do not print URLs.

### Local services exposed to LAN

**Risk:** development database/cache are reachable from other hosts.

**Mitigation:** Compose host ports bind to `127.0.0.1`.

### ORM design begins before domain persistence design

**Risk:** database schema dictates domain design.

**Mitigation:** SQLAlchemy is used only for the engine/pool and `SELECT 1`; no ORM model exists.

### Redis gains accidental business responsibility

**Risk:** architecture starts depending on cache semantics without requirements.

**Mitigation:** Redis has only lifecycle/readiness behavior in S0-007.

## 17. Definition of Done

S0-007 is complete when:

```bash
uv lock
uv sync --locked --group dev
docker compose config
docker compose up -d
docker compose ps
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

pass, the live dependency test passes when enabled, CI is green, and manually stopping either
dependency produces:

```text
/health -> 200
/ready  -> 503
```
