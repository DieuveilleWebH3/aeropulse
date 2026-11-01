# AeroPulse

**Predictive Maintenance & Fleet Health Monitoring Platform**

AeroPulse is an engineering portfolio project demonstrating the design of a production-oriented predictive-maintenance platform with Python, FastAPI, event-driven processing, data engineering, observability, security, testing, and cloud infrastructure.

> Current status: **Sprint 1 — Aircraft Lifecycle / Retirement**

## Current bootstrap

The engineering foundation is complete and AeroPulse has entered its first business sprint. The current implementation includes FastAPI, PostgreSQL, Redis, dynamic liveness/readiness, and the first Fleet domain capability: aircraft registration.

## Current business capability

### Aircraft registration domain

Sprint 1 introduces the first Fleet bounded-context use case:

```text
RegisterAircraftCommand
        ↓
AircraftRegistration validation / normalization
        ↓
duplicate-registration check
        ↓
Aircraft aggregate creation
        ↓
AircraftRepository port
```

Current domain guarantees include:

- canonical uppercase aircraft registrations;
- explicit V1 registration validation;
- new aircraft start in `ACTIVE` state;
- timezone-aware creation timestamps normalized to UTC;
- aircraft registration is read-only after creation;
- duplicate registration is represented as an application-level business error.

S1-002 persists aircraft through PostgreSQL/SQLAlchemy, versions the schema with Alembic,
and enforces canonical registration uniqueness with a database constraint.

S1-003 exposes the first business API endpoint:

```text
POST /api/v1/aircraft
```

with transaction-scoped persistence and stable `409` / `422` business error contracts.

### Prerequisites

- `uv >= 0.13.6, < 0.14`
- CPython `3.14.10` (uv can install it)

### Setup

```bash
uv python install 3.14.10
uv lock
uv sync --locked
```

Install local Git hooks:

```bash
uv run --locked pre-commit install
```

### Verify the package

```bash
uv run --locked python -c "import aeropulse; print(aeropulse.__name__)"
```

Expected:

```text
aeropulse
```

### Start local dependencies

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Start PostgreSQL and Redis:

```bash
docker compose up -d
docker compose ps
```

### Database migrations

Install migration tooling with the project environment:

```bash
uv sync --locked --group migration
```

Apply the current schema:

```bash
uv run --locked --group migration alembic upgrade head
```

Verify metadata and migration history remain aligned:

```bash
uv run --locked --group migration alembic check
```


S1-004 ends at migration:

```text
20261101_0003
```

which normalizes the historical aircraft-status check-constraint name.

After S1-005, the expected Alembic head is:

```text
20261101_0004
```

which adds aircraft retirement persistence and lifecycle consistency protection.

### Run the API

```bash
uv run --locked uvicorn aeropulse.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

Operational probes:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/ready
```

### Register an aircraft

Use the example for your shell. PowerShell and bash do not handle native-command quoting in exactly
the same way.

#### Windows PowerShell — recommended

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

To inspect the raw status and headers, use `Invoke-WebRequest` with the same `$body`.

#### Windows PowerShell — `curl.exe` alternative

```powershell
curl.exe -i -X POST http://127.0.0.1:8000/api/v1/aircraft `
  -H "Content-Type: application/json" `
  --data-raw "{`"registration`":`"F-HABC`"}"
```

Do **not** use the bash-oriented `-d '{"registration":"F-HABC"}'` form with native Windows
`curl.exe`; shell quoting can turn it into malformed JSON and FastAPI will return a framework-level
`422` with `type: "json_invalid"` before the Fleet use case runs.

#### Bash / Git Bash / WSL

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/aircraft \
  -H "Content-Type: application/json" \
  -d '{"registration":"F-HABC"}'
```

Expected success:

```text
HTTP/1.1 201 Created
```

```json
{
  "id": "<uuid>",
  "registration": "F-HABC",
  "status": "active",
  "created_at": "<utc timestamp>",
  "retired_at": null
}
```

For duplicate and invalid-registration checks in both shells, see
[Fleet aircraft registration HTTP API](docs/architecture/fleet-http-api.md#12-manual-validation).

### Retrieve and list aircraft

#### Windows PowerShell

List the fleet and capture a real aircraft UUID from the response:

```powershell
$fleet = Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/aircraft?limit=50&offset=0"

$fleet.items
$aircraftId = $fleet.items[0].id
```

Retrieve that aircraft:

```powershell
Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/aircraft/$aircraftId"
```

Do not send the literal text `<aircraft-uuid>` in the URL. It is documentation notation, not a
valid UUID, and FastAPI will correctly return a UUID parsing `422`.

#### Bash / Git Bash / WSL

List aircraft:

```bash
curl -i "http://127.0.0.1:8000/api/v1/aircraft?limit=50&offset=0"
```

Then copy an actual `id` returned in `items` into a shell variable:

```bash
AIRCRAFT_ID="fae526e4-10de-4371-bad5-c7028695992d"
curl -i "http://127.0.0.1:8000/api/v1/aircraft/${AIRCRAFT_ID}"
```

The UUID above is only an example; use an ID returned by your local AeroPulse API.

### Retire an aircraft

#### Windows PowerShell

Capture a real aircraft ID, then retire it:

```powershell
$fleet = Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/aircraft?limit=50&offset=0"

$aircraftId = $fleet.items[0].id

$retired = Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/aircraft/$aircraftId/retire" `
    -Method Post

$retired
```

Calling the same endpoint again is safe and returns the same `retired_at` timestamp.

#### Bash / Git Bash / WSL

```bash
AIRCRAFT_ID="replace-with-a-real-aircraft-uuid"

curl -i -X POST \
  "http://127.0.0.1:8000/api/v1/aircraft/${AIRCRAFT_ID}/retire"
```

Expected:

```text
200 OK
status = retired
retired_at = <utc timestamp>
```

### Quality checks

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

Run local hook suites manually:

```bash
uv run --locked pre-commit run --all-files
uv run --locked pre-commit run --all-files --hook-stage pre-push
```

### Continuous integration

Pull requests and pushes to `main` run the same non-mutating quality gates in GitHub Actions:

```text
uv.lock check → Ruff lint → Ruff format check → mypy → pytest/coverage
```

The required status check is designed to be:

```text
CI / quality
```

See [Continuous integration](docs/engineering/continuous-integration.md) for security, caching, concurrency, and branch-protection guidance.

### Build

```bash
uv build
```

## Engineering documentation

- [Repository architecture](docs/architecture/repository-structure.md)
- [Copilot agent strategy](docs/engineering/copilot-agent-strategy.md)
- [Python toolchain](docs/engineering/python-toolchain.md)
- [Code quality and testing](docs/engineering/quality-and-testing.md)
- [Continuous integration](docs/engineering/continuous-integration.md)
- [FastAPI application bootstrap](docs/engineering/fastapi-application-bootstrap.md)
- [Local runtime dependencies](docs/engineering/local-runtime-dependencies.md)
- [Fleet domain — aircraft registration](docs/architecture/fleet-domain.md)
- [Fleet persistence](docs/architecture/fleet-persistence.md)
- [Fleet aircraft registration HTTP API](docs/architecture/fleet-http-api.md)
- [Fleet aircraft read API](docs/architecture/fleet-read-api.md)
- [Fleet aircraft lifecycle](docs/architecture/fleet-lifecycle.md)

## Foundation roadmap

- [x] S0-001 — Repository architecture and engineering guardrails
- [x] S0-002 — Copilot agent governance and repository instructions
- [x] S0-003 — Python + uv project bootstrap
- [x] S0-004 — Code quality and test toolchain
- [x] S0-005 — Minimal GitHub Actions CI
- [x] S0-006 — FastAPI application with `/health` and `/ready`
- [x] S0-007 — Local dependencies and Docker Compose

## Sprint 1 — Fleet & Asset Management

- [x] S1-001 — Aircraft domain model and registration use case
- [x] S1-002 — PostgreSQL aircraft persistence and Alembic
- [x] S1-003 — Aircraft registration HTTP API
- [x] S1-004 — Retrieve and list aircraft
- [x] S1-005 — Aircraft lifecycle / retirement
- [ ] S1-006 — Equipment domain and persistence
- [ ] S1-007 — Equipment HTTP API
- [ ] S1-008 — Fleet integration and E2E validation

## License

AeroPulse is released under the [MIT License](LICENSE).

The project is an engineering demonstrator and does not claim certified aerospace,
airworthiness, or maintenance-decision authority.
