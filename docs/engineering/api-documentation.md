# AeroPulse API Documentation Experience

## Purpose

AeroPulse uses FastAPI's generated OpenAPI documentation rather than maintaining a separate
frontend solely for API exploration.

This keeps the project lightweight while still providing an interactive, professional API
surface for engineers, reviewers, and portfolio visitors.

## Documentation surfaces

When the API is running locally:

```text
Swagger UI   http://127.0.0.1:8000/docs
ReDoc        http://127.0.0.1:8000/redoc
OpenAPI JSON http://127.0.0.1:8000/openapi.json
```

Swagger UI is the primary interactive interface because it allows callers to inspect schemas
and execute requests directly from the browser.

ReDoc provides a more documentation-oriented read-only presentation.

## OpenAPI metadata

The application publishes:

- project title and version;
- a PHM/Fleet platform summary;
- a longer architecture/product description;
- the MIT license identifier;
- ordered `aircraft` and `equipment` tag descriptions.

Operational endpoints remain excluded from OpenAPI:

```text
/health
/ready
```

They are infrastructure probes rather than public business API operations.

## Swagger usability settings

AeroPulse enables:

```text
deep linking
request-duration display
tag filtering
persistent authorization state
Try It Out
list-style operation expansion
```

These options improve developer ergonomics without introducing custom JavaScript/CSS or a
frontend build toolchain.

## Why not build a custom UI in Sprint 1?

A dedicated frontend would introduce a second application stack, deployment surface, dependency
graph, and test strategy before AeroPulse has user-facing PHM visualizations that justify it.

A custom dashboard becomes valuable later when the product has data that benefits from visual
interaction, such as:

- fleet health summaries;
- time-series telemetry;
- anomaly timelines;
- degradation and RUL curves;
- maintenance recommendations;
- work-order status;
- operational alerts.

Until those capabilities exist, OpenAPI/Swagger provides the appropriate engineering interface.

## Security direction

Interactive documentation is useful in local/development environments. Before a public
production deployment, the project should explicitly decide whether OpenAPI/Swagger/ReDoc remain
enabled, are authenticated, or are disabled by environment policy.

That decision belongs with the later authentication/security deployment stories rather than
being hard-coded in Sprint 1.

## Tests

Integration tests verify:

- `/docs` is available;
- `/redoc` is available;
- `/openapi.json` is available;
- OpenAPI metadata contains the expected project summary/license;
- Fleet tags appear in the intended order;
- `/health` and `/ready` remain excluded from the schema.
