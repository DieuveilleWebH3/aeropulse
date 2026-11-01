# AeroPulse — Equipment HTTP API

**Ticket:** S1-007 — Equipment HTTP API
**Sprint:** 1 — Fleet & Asset Management

## Purpose

S1-007 exposes the S1-006 Equipment domain and persistence capabilities through FastAPI.

No new database migration is required. The S1-006 schema at Alembic head `20261101_0005`
already contains the Equipment table, foreign key, uniqueness constraint, and deterministic
listing index.

## Endpoints

Register equipment:

```text
POST /api/v1/aircraft/{aircraft_id}/equipment
```

Retrieve equipment:

```text
GET /api/v1/equipment/{equipment_id}
```

List equipment for one aircraft:

```text
GET /api/v1/aircraft/{aircraft_id}/equipment?limit=50&offset=0
```

## Registration contract

Request:

```json
{
  "equipment_type": "engine-control",
  "part_number": "PN-ab/01",
  "serial_number": "Sn-00a"
}
```

Success:

```text
201 Created
```

```json
{
  "id": "<uuid>",
  "aircraft_id": "<uuid>",
  "equipment_type": "ENGINE-CONTROL",
  "part_number": "PN-ab/01",
  "serial_number": "Sn-00a",
  "created_at": "<utc timestamp>"
}
```

`equipment_type` is returned in canonical AeroPulse form. Manufacturer-issued part and serial
numbers preserve case after surrounding whitespace is trimmed by the domain value objects.

## Error contract

```text
unknown aircraft                         -> 404 aircraft_not_found
unknown equipment                        -> 404 equipment_not_found
duplicate part-number/serial-number pair -> 409 equipment_already_exists
retired parent aircraft                  -> 409 aircraft_retired_for_equipment_registration
invalid equipment type                   -> 422 invalid_equipment_type
invalid part number                      -> 422 invalid_equipment_part_number
invalid serial number                    -> 422 invalid_equipment_serial_number
malformed UUID                           -> FastAPI framework 422
invalid pagination                       -> FastAPI framework 422
```

Domain errors remain the authority for business validation. Pydantic validates HTTP structure
and rejects unknown request fields; it does not duplicate Equipment regex/domain policy.

## Transaction model

Registration reuses the existing function-scoped transaction dependency:

```text
request
  -> AsyncSession
  -> transaction
  -> RegisterEquipmentHandler
  -> Aircraft SELECT FOR UPDATE
  -> Equipment INSERT
  -> commit
  -> response
```

This preserves the S1-006 race protection between equipment registration and aircraft
retirement.

## Read semantics

Equipment lookup by Equipment UUID returns `404 equipment_not_found` when absent.

The nested list endpoint first verifies the parent Aircraft exists. This means:

```text
existing aircraft with zero equipment -> 200, empty items
missing aircraft                      -> 404
```

Returning an empty collection for a missing parent would hide a resource-identity error.

## Pagination

Equipment uses the same initial bounded offset pagination policy as Aircraft:

```text
default limit = 50
minimum limit = 1
maximum limit = 100
minimum offset = 0
```

Persistence remains deterministically ordered by:

```text
created_at ASC
id ASC
```

Large-scale cursor/keyset pagination remains a later optimization when measured access patterns
justify it.

## OpenAPI grouping

S1-007 removes the router-wide `aircraft` tag and assigns tags per operation:

```text
aircraft endpoints  -> aircraft
equipment endpoints -> equipment
```

This keeps generated API documentation navigable as Fleet grows.

## Tests

Contract tests verify:

- `201` Equipment registration response;
- canonicalized Equipment type;
- preserved part/serial identifier case;
- `404`, `409`, and domain `422` mappings;
- Equipment retrieval;
- paginated Equipment listing;
- pagination validation;
- OpenAPI path exposure.

Live PostgreSQL API tests verify:

- Aircraft registration -> Equipment registration -> Equipment GET;
- nested Equipment listing;
- duplicate Equipment identity conflict;
- retired Aircraft rejection;
- missing parent/equipment read behavior.

## Non-goals

S1-007 does not implement:

- moving Equipment between aircraft;
- Equipment lifecycle/removal;
- Equipment updates;
- authentication/authorization;
- telemetry ingestion;
- Equipment search across the full fleet;
- cursor pagination.

## Definition of Done

```bash
uv lock --check
uv run --locked --group migration alembic current
uv run --locked --group migration alembic check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

Expected migration head remains:

```text
20261101_0005
```
