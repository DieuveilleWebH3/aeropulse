# Contributing to AeroPulse

Thank you for contributing to AeroPulse.

AeroPulse is a production-oriented aircraft PHM engineering demonstrator. Changes
should improve not only functionality, but also maintainability, reliability,
security, testability, and architectural clarity.

By participating, you agree to follow `CODE_OF_CONDUCT.md`.

## Before contributing

- Search existing issues and pull requests first.
- Use `SECURITY.md` for vulnerabilities; never disclose exploit details publicly.
- Do not contribute proprietary, customer, airline, export-controlled, or confidential
  aircraft data.
- Use public or synthetic data for tests and examples.

## Development environment

Baseline:

```text
CPython 3.14.10
uv >= 0.13.6, < 0.14
PostgreSQL 18
Redis 8
```

Bootstrap:

```bash
uv python install 3.14.10
uv sync --locked --group dev --group migration
uv run --locked pre-commit install
docker compose up -d
```

Apply migrations:

```bash
uv run --locked --group migration alembic upgrade head
uv run --locked --group migration alembic check
```

## Branching

Create a focused branch from the latest `main`.

Examples:

```text
sprint-1/s1-006-equipment-persistence
fix/db-constraint-name
docs/security-policy
```

Keep unrelated changes in separate pull requests.

## Architecture rules

AeroPulse currently follows a modular-monolith architecture:

```text
Presentation
    ↓
Application
    ↓
Domain

Infrastructure implements inward-owned ports.
```

Required guardrails:

- domain code must not depend on FastAPI, SQLAlchemy, Alembic, Redis, boto3, or HTTP clients;
- application code must not depend on presentation/infrastructure frameworks;
- infrastructure implements inward-owned ports;
- routes remain thin and do not contain business rules;
- avoid generic `utils.py` dumping grounds;
- prefer explicit types and focused interfaces;
- apply SOLID, KISS, DRY, and YAGNI pragmatically.

## Database migrations

Migration history is append-only after a revision has been shared or applied.

Do not rewrite an older Alembic revision to fix a later-discovered schema problem.
Create a new corrective migration instead.

Before submitting database changes:

```bash
uv run --locked --group migration alembic upgrade head
uv run --locked --group migration alembic current
uv run --locked --group migration alembic check
```

Use deterministic, explicitly named constraints and indexes.

## Testing and quality gates

Every contribution must pass:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
uv lock --check
```

When PostgreSQL/Redis integration tests are required:

PowerShell:

```powershell
$env:AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS = "1"
```

Bash:

```bash
export AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1
```

Then rerun `pytest`.

For complete user-visible workflows, run the registered E2E suite explicitly:

```bash
uv run --locked pytest -m e2e
```

New behavior should have tests at the lowest useful level:

- domain unit tests for invariants;
- application unit tests for orchestration/business outcomes;
- repository/infrastructure integration tests for database contracts;
- HTTP contract/integration tests for exposed APIs;
- E2E tests for complete assembled user-visible workflows;
- failure/concurrency tests where correctness depends on races or retries.

The project requires at least 90% coverage, but meaningful assertions are more
important than coverage inflation.

## Typing and linting

Strict mypy is part of the project contract.

Do not silence a real typing or linting problem with `# type: ignore`, `noqa`, or
disabled rules merely to make CI pass. Fix the design or narrow the type correctly.

## Documentation

Update relevant documentation whenever a change affects:

- public API contracts;
- architecture;
- migrations;
- operational commands;
- security;
- developer workflow;
- business invariants.

PowerShell and bash examples should be separated when shell quoting differs.

## Commit messages

Use concise Conventional-Commit-style messages.

Examples:

```text
feat(fleet): add equipment persistence
fix(db): normalize aircraft status constraint name
docs(api): clarify PowerShell examples
test(fleet): cover equipment identity conflict
```

## Pull requests

A pull request should explain:

- need/problem;
- implementation approach;
- risks;
- mitigations;
- validation performed;
- migration or compatibility impact.

Checklist:

- [ ] change is focused;
- [ ] architecture boundaries are preserved;
- [ ] migrations are forward-only and reversible where practical;
- [ ] tests cover new behavior and important failure paths;
- [ ] Ruff passes;
- [ ] formatting passes;
- [ ] strict mypy passes;
- [ ] pytest passes;
- [ ] `uv lock --check` passes;
- [ ] documentation is updated;
- [ ] no secrets or confidential data are included.

## Review philosophy

Reviews should focus on correctness, maintainability, security, architectural
boundaries, failure behavior, and clarity. Prefer constructive technical arguments
over stylistic preference when automated formatting already defines the style.
