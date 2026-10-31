# AeroPulse — Python Toolchain

**Ticket:** S0-003 — Python + uv project bootstrap
**Status:** Accepted for Sprint 0

## 1. Purpose

This document defines the initial Python runtime and package-management baseline for AeroPulse.

The objective is reproducibility without introducing application dependencies before they are required.

## 2. Selected Baseline

| Concern | Decision |
|---|---|
| Python development runtime | CPython 3.14.10 |
| Supported Python minor | 3.14.x |
| Package/environment manager | uv |
| Minimum uv version | 0.13.6 |
| uv compatibility window | `>=0.13.6,<0.14` |
| Build backend | `uv_build` |
| Python source layout | `src/` |
| Lock file | `uv.lock`, committed |

## 3. Why Python 3.14 Instead of 3.15?

Python 3.15 is current, but it became stable only in October 2026.

AeroPulse will later integrate a relatively broad ecosystem:

- FastAPI / Pydantic;
- PostgreSQL drivers and SQLAlchemy;
- Kafka clients;
- PySpark;
- MLflow;
- scientific / ML packages.

A newly released Python minor can temporarily have incomplete binary-wheel or framework support across that ecosystem.

Python 3.14 remains in active bugfix support and gives AeroPulse a modern runtime with a more mature compatibility surface.

This is a deliberate risk-management choice, not a permanent rejection of Python 3.15.

## 4. Version Policy

`.python-version` pins the developer runtime to:

```text
3.14.10
```

`pyproject.toml` declares:

```toml
requires-python = ">=3.14,<3.15"
```

This means:

- developers use the same patch release by default;
- package metadata accurately states that AeroPulse currently targets Python 3.14;
- code may safely use Python 3.14 language/runtime capabilities;
- a Python 3.15 migration is an explicit engineering change rather than an accidental environment upgrade.

## 5. uv Policy

AeroPulse uses uv for:

- Python environment creation;
- dependency resolution;
- lock-file generation;
- command execution;
- package building.

`pyproject.toml` requires:

```toml
[tool.uv]
required-version = ">=0.13.6,<0.14"
```

The lower bound is selected because uv 0.13.6 includes the CPython 3.14.10 managed runtime.

The upper bound avoids silently adopting a future uv minor with breaking behavior before validating it.

Updating the uv compatibility window should be a dedicated platform/tooling change.

## 6. Build Backend

The project uses:

```toml
[build-system]
requires = ["uv_build>=0.13.6,<0.14"]
build-backend = "uv_build"
```

AeroPulse is currently pure Python, so the native uv build backend is sufficient and keeps the bootstrap simple.

If native extension or unusual packaging requirements emerge later, the build backend can be revisited with evidence.

## 7. Dependency Policy

S0-003 intentionally defines:

```toml
dependencies = []
```

Runtime dependencies are introduced only by the ticket that needs them.

Examples:

- FastAPI belongs to S0-006;
- pytest/Ruff/mypy belong to S0-004;
- PostgreSQL libraries belong to the first persistence ticket;
- Kafka libraries belong to the event-processing sprint.

This follows YAGNI and makes dependency ownership traceable.

## 8. Lock-File Policy

`uv.lock` is committed to Git.

Normal developer setup:

```bash
uv sync --locked
```

CI should also use locked resolution once CI is introduced.

The lock file is updated intentionally with commands such as:

```bash
uv lock
```

or, for a controlled upgrade:

```bash
uv lock --upgrade-package <package>
```

Do not manually edit transitive dependency entries in `uv.lock`.

## 9. New Developer Bootstrap

Install a compatible uv release, then from the repository root:

```bash
uv python install 3.14.10
uv sync --locked
```

Validate package import:

```bash
uv run --locked python -c "import aeropulse; print(aeropulse.__name__)"
```

Expected output:

```text
aeropulse
```

Validate packaging:

```bash
uv build
```

## 10. Upgrade Policy

### Python patch upgrade

Example: 3.14.10 → later 3.14.x.

Expected work:

1. update `.python-version`;
2. regenerate/check lock state;
3. run the full validation suite;
4. verify Docker/CI runtime consistency once those exist.

### Python minor upgrade

Example: 3.14 → 3.15.

Treat as a dedicated engineering ticket.

Validate at minimum:

- FastAPI / Pydantic;
- SQLAlchemy and PostgreSQL driver;
- Kafka client;
- PySpark;
- MLflow;
- scientific/ML dependencies;
- test/tooling compatibility;
- container base images;
- CI runners.

Update `requires-python` only after the supported ecosystem has been validated.

## 11. Non-goals of S0-003

This ticket does not add:

- FastAPI;
- Pydantic;
- pytest;
- Ruff;
- mypy;
- pre-commit;
- SQLAlchemy;
- database drivers;
- Kafka;
- ML libraries.

Those are introduced by later tickets where their requirements and validation strategy are known.
