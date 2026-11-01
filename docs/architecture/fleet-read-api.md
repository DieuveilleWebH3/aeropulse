
# AeroPulse — Retrieve & List Aircraft

**Ticket:** S1-004 — Retrieve & List Aircraft
**Sprint:** 1 — Fleet & Asset Management

## Purpose

S1-004 adds the read side of the Fleet aircraft vertical slice:

```text
GET /api/v1/aircraft/{aircraft_id}
GET /api/v1/aircraft?limit=50&offset=0
```

The domain remains independent from FastAPI and SQLAlchemy.

## Retrieve one aircraft

A stable UUID identifies the aircraft:

```text
GET /api/v1/aircraft/{aircraft_id}
```

Existing aircraft return `200 OK` with the same `AircraftResponse` contract used by registration.

Missing aircraft return:

```text
404 Not Found
```

with:

```json
{
  "error": {
    "code": "aircraft_not_found",
    "message": "aircraft not found: <uuid>",
    "field": null
  }
}
```

Malformed UUID path values are framework validation failures and remain FastAPI `422` responses.

## List aircraft

The initial collection API uses bounded offset pagination:

```text
GET /api/v1/aircraft?limit=50&offset=0
```

Defaults and limits:

```text
limit default = 50
limit minimum = 1
limit maximum = 100
offset minimum = 0
```

Response:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

## Deterministic ordering

Database pages are ordered by:

```text
created_at ASC
id ASC
```

The UUID tie-breaker prevents non-deterministic ordering when multiple rows share the same
creation timestamp.

S1-004 adds the PostgreSQL index:

```text
ix_aircraft_created_at_id (created_at, id)
```

through Alembic revision `20261101_0002`.

## Why offset pagination first?

Fleet aircraft collections are currently small compared with future telemetry datasets. Offset
pagination is understandable, easy to consume, and sufficient for the current access pattern.

It is not presented as the final high-scale design. Large offsets become increasingly expensive and
concurrent inserts can shift page boundaries. When measured fleet/query volume justifies it, the API
can migrate to cursor/keyset pagination using the same deterministic `(created_at, id)` ordering.

## Read repository interface segregation

S1-004 does **not** expand the aircraft-registration repository port into a large catch-all interface.

The domain now exposes two capabilities:

```text
AircraftRepository
  exists_by_registration
  add

AircraftReadRepository
  get_by_id
  list_aircraft
  count_aircraft
```

The SQLAlchemy adapter implements both structurally.

This keeps registration-only test doubles and future implementations from depending on read methods
they do not use.

## Rehydration

A newly registered Aircraft must always start `ACTIVE`, so its normal constructor still does not
accept arbitrary lifecycle status.

Read persistence needs to restore historical state, including future `RETIRED` aircraft. The domain
therefore exposes:

```text
Aircraft.rehydrate(..., status=...)
```

for trusted persisted state.

This separates:

```text
new aggregate creation
```

from:

```text
existing aggregate restoration
```

without making registration status user-controlled.

## Consistency note

The list handler currently executes one page query and one count query in the same request
transaction. Under PostgreSQL's default `READ COMMITTED` isolation, each statement may observe a
newer committed snapshot. Therefore `total` is a current pagination aid, not a historical snapshot
contract under concurrent writes.

That tradeoff is acceptable for the current Fleet use case and is explicitly documented rather than
hidden behind unnecessary transaction isolation complexity.

## Manual validation

Before testing, ensure the API is running and the S1-004 migration is applied.

### Windows PowerShell

List aircraft and keep the response:

```powershell
$fleet = Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/aircraft?limit=50&offset=0"
```

Inspect the collection:

```powershell
$fleet.items
```

Capture a real UUID from the returned data:

```powershell
$aircraftId = $fleet.items[0].id
```

Retrieve that aircraft:

```powershell
Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/aircraft/$aircraftId"
```

Expected:

```text
200 OK
```

If the collection is empty, register an aircraft first with `POST /api/v1/aircraft`, then list again.

Do **not** invoke:

```text
/api/v1/aircraft/<aircraft-uuid>
```

literally. Angle-bracket notation means “substitute a real value”. Sending it unchanged produces a
FastAPI UUID parsing `422` before the Fleet retrieval use case runs.

### Bash / Git Bash / WSL

List aircraft:

```bash
curl -i "http://127.0.0.1:8000/api/v1/aircraft?limit=50&offset=0"
```

Copy a real aircraft `id` from the response, then:

```bash
AIRCRAFT_ID="fae526e4-10de-4371-bad5-c7028695992d"
curl -i "http://127.0.0.1:8000/api/v1/aircraft/${AIRCRAFT_ID}"
```

Replace the example UUID with an ID returned by your local API.

### Not-found behavior

Use a valid UUID that is not present in the database:

```powershell
$missingId = "00000000-0000-4000-8000-000000000000"

try {
    Invoke-RestMethod `
        -Uri "http://127.0.0.1:8000/api/v1/aircraft/$missingId"
} catch {
    $_.Exception.Response.StatusCode
    $_.ErrorDetails.Message
}
```

Expected business result:

```text
404 Not Found
```

A malformed UUID is different: it is a framework-level path-validation error and returns `422`.


## Check-constraint naming correction

S1-004 CI exposed a schema naming mismatch on PostgreSQL.

The metadata naming convention is:

```text
ck_%(table_name)s_%(constraint_name)s
```

The status constraint was already passed as the complete intended name:

```text
ck_aircraft_status
```

Without marking that name as already converted, SQLAlchemy applied the convention again and the
database received:

```text
ck_aircraft_ck_aircraft_status
```

The SQLAlchemy metadata now uses:

```python
name = conv(AIRCRAFT_STATUS_CHECK_CONSTRAINT)
```

so the final metadata name remains:

```text
ck_aircraft_status
```

Migration `20261101_0003` preserves existing migration history and converges both database states
that can exist in development/CI:

```text
ck_aircraft_ck_aircraft_status -> rename to ck_aircraft_status
ck_aircraft_status             -> already correct; no-op
both names present             -> keep canonical and remove the duplicate historical name
neither name present           -> fail loudly as genuine schema drift
```

This state-aware migration is necessary because some databases were originally created with the
canonical explicit migration name, while SQLAlchemy naming-convention processing produced the
doubled name in other environments.

The S1-004 migration head is therefore now:

```text
20261101_0003
```

## Validation

S1-004 tests:

- domain rehydration of persisted lifecycle state;
- application retrieval and `AircraftNotFound` behavior;
- application pagination constraints;
- PostgreSQL row-to-domain mapping;
- deterministic limit/offset ordering;
- migrated list index;
- `200`, `404`, and pagination HTTP contracts;
- live API -> application -> PostgreSQL retrieval/listing.

## Non-goals

S1-004 does not add:

- search by registration;
- sorting selected by clients;
- cursor pagination;
- filtering by status;
- aircraft updates;
- retirement behavior;
- caching.

Those should be introduced only with concrete use cases.
