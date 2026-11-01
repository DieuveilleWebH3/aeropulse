# AeroPulse — Fleet Aircraft Registration HTTP API

**Ticket:** S1-003 — Aircraft Registration HTTP API
**Sprint:** 1 — Fleet & Asset Management
**Status:** Accepted for implementation

## 1. Purpose

S1-003 exposes the existing aircraft-registration use case through the first public Fleet HTTP
endpoint:

```text
POST /api/v1/aircraft
```

The route is intentionally thin:

```text
HTTP request
    |
    v
Pydantic request schema
    |
    v
FastAPI dependency composition
    |
    v
RegisterAircraftHandler
    |
    v
SqlAlchemyAircraftRepository
    |
    v
PostgreSQL
    |
    v
HTTP 201 response
```

Business rules remain in the Fleet domain/application layers.

## 2. Request

```http
POST /api/v1/aircraft
Content-Type: application/json

{
  "registration": " f-habc "
}
```

Unknown request fields are rejected.

The HTTP schema deliberately does not duplicate aircraft-registration business validation. The
domain `AircraftRegistration` value object remains the authoritative validator and normalizer.

## 3. Success Response

Status:

```text
201 Created
```

Body:

```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "registration": "F-HABC",
  "status": "active",
  "created_at": "2026-11-01T10:00:00Z"
}
```

`registration` is returned in canonical domain form.

## 4. Stable Business Error Contract

Invalid registration:

```text
422 Unprocessable Content
```

```json
{
  "error": {
    "code": "invalid_aircraft_registration",
    "message": "...",
    "field": "registration"
  }
}
```

Duplicate registration:

```text
409 Conflict
```

```json
{
  "error": {
    "code": "aircraft_registration_already_exists",
    "message": "aircraft registration already exists: F-HABC",
    "field": "registration"
  }
}
```

Error `code` is intended for machine handling. `message` remains human-readable.

Framework-level request validation failures continue to use FastAPI's normal validation error
contract.

## 5. Exception Translation

Business exceptions are registered as application-level FastAPI exception handlers.

The route does not catch:

```text
InvalidAircraftRegistration
AircraftRegistrationAlreadyExists
```

itself.

This is intentional because the exception must first propagate through the transaction-scoped
dependency so SQLAlchemy can roll back before FastAPI converts the exception into an HTTP
response.

Catching a database-backed business exception inside the route could make the transaction
context appear successful and attempt a commit after a failed database operation.

## 6. Transaction Scope

One request use case gets one `AsyncSession` and one transaction:

```python
session = resources.create_database_session()

async with session, session.begin():
    yield session
```

The dependency is declared with:

```python
Depends(get_database_session, scope="function")
```

This is critical.

With FastAPI's default request-scoped `yield` dependency, cleanup happens after the response is
sent. A database transaction must instead commit or roll back before the response is sent so a
failed commit cannot follow an already-delivered `201 Created`.

`scope="function"` runs dependency exit code after the route returns but before response delivery.

## 7. Session Ownership

Runtime resources own the SQLAlchemy async engine and `async_sessionmaker`.

Each HTTP unit of work calls:

```text
create_database_session()
```

to receive a fresh `AsyncSession`.

Sessions are never stored globally and are never shared between concurrent requests.

## 8. Dependency Composition

The presentation dependency composes:

```text
AsyncSession
    ↓
SqlAlchemyAircraftRepository
    ↓
RegisterAircraftHandler
```

The route sees only the application handler.

It does not construct SQLAlchemy engines, sessions, or repositories itself.

## 9. Versioning

Public business routes are prefixed:

```text
/api/v1
```

Operational endpoints remain unversioned:

```text
/health
/ready
```

because they are infrastructure contracts rather than business API resources.

## 10. Tests

Database-free HTTP contract tests verify:

- `201` response shape;
- duplicate `409` error contract;
- invalid registration `422` error contract;
- unknown request fields are rejected;
- OpenAPI documents `201`, `409`, and `422`.

Live PostgreSQL integration tests verify:

- `POST /api/v1/aircraft` persists the canonical aircraft;
- persistence is committed before the `201` is observed;
- duplicate canonical registration returns `409`;
- only one database row remains for the duplicate case.

## 11. Non-goals

S1-003 does not implement:

- `GET /api/v1/aircraft/{id}`;
- aircraft listing;
- pagination;
- update;
- retirement;
- authentication/authorization;
- idempotency keys;
- rate limiting.

These belong to later stories.


## 12. Manual Validation

Before exercising the endpoint, make sure PostgreSQL is running, the current Alembic migration has
been applied, and Uvicorn is listening on `127.0.0.1:8000`.

### Windows PowerShell — recommended

Prefer PowerShell-native JSON serialization so shell quoting cannot corrupt the request body:

```powershell
$body = @{
    registration = "F-HABC"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/aircraft" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Expected parsed response:

```json
{
  "id": "<uuid>",
  "registration": "F-HABC",
  "status": "active",
  "created_at": "<utc timestamp>"
}
```

To inspect the raw HTTP status and headers instead, use `Invoke-WebRequest`:

```powershell
$body = @{
    registration = "F-HABC"
} | ConvertTo-Json

Invoke-WebRequest `
    -Uri "http://127.0.0.1:8000/api/v1/aircraft" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Windows PowerShell — `curl.exe` alternative

When calling native `curl.exe`, escape the embedded JSON double quotes explicitly:

```powershell
curl.exe -i -X POST http://127.0.0.1:8000/api/v1/aircraft `
  -H "Content-Type: application/json" `
  --data-raw "{`"registration`":`"F-HABC`"}"
```

Do **not** copy the bash form below directly into native Windows `curl.exe`:

```text
-d '{"registration":"F-HABC"}'
```

Native-command quoting can cause malformed JSON to reach FastAPI. A response such as:

```json
{
  "detail": [
    {
      "type": "json_invalid",
      "msg": "JSON decode error"
    }
  ]
}
```

means the HTTP body could not be parsed. It is a framework-level request parsing failure; the Fleet
registration use case was **not** executed.

### Bash / Git Bash / WSL

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/aircraft \
  -H "Content-Type: application/json" \
  -d '{"registration":"F-HABC"}'
```

Expected:

```text
HTTP/1.1 201 Created
```

### Duplicate-registration check

PowerShell:

```powershell
$body = @{
    registration = " f-habc "
} | ConvertTo-Json

try {
    Invoke-RestMethod `
        -Uri "http://127.0.0.1:8000/api/v1/aircraft" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
} catch {
    $_.Exception.Response.StatusCode
    $_.ErrorDetails.Message
}
```

Bash:

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/aircraft \
  -H "Content-Type: application/json" \
  -d '{"registration":" f-habc "}'
```

Expected:

```text
409 Conflict
```

with application error code:

```text
aircraft_registration_already_exists
```

### Invalid-domain-registration check

PowerShell:

```powershell
$body = @{
    registration = "F/HABC"
} | ConvertTo-Json

try {
    Invoke-RestMethod `
        -Uri "http://127.0.0.1:8000/api/v1/aircraft" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body
} catch {
    $_.Exception.Response.StatusCode
    $_.ErrorDetails.Message
}
```

Bash:

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/aircraft \
  -H "Content-Type: application/json" \
  -d '{"registration":"F/HABC"}'
```

Expected:

```text
422 Unprocessable Content
```

with application error code:

```text
invalid_aircraft_registration
```

This domain-level `422` is intentionally different from FastAPI's `json_invalid` response: the
former means valid JSON reached the Fleet use case and violated a business invariant; the latter
means the JSON body could not be decoded at all.

## 13. Definition of Done

S1-003 is complete when:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked --group migration alembic upgrade head
uv run --locked --group migration alembic check
uv run --locked pytest
```

pass, CI is green, and the live API returns:

```text
valid registration     -> 201
duplicate registration -> 409
invalid registration   -> 422
```
