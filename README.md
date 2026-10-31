# AeroPulse

**Predictive Maintenance & Fleet Health Monitoring Platform**

AeroPulse is an engineering portfolio project demonstrating the design of a production-oriented predictive-maintenance platform with Python, FastAPI, event-driven processing, data engineering, observability, security, testing, and cloud infrastructure.

> Current status: **Sprint 0 — Foundation / CI enabled**

## Current bootstrap

The repository currently establishes the Python package and engineering-quality foundation. Application runtime dependencies such as FastAPI are intentionally introduced in later tickets.

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

## Foundation roadmap

- [x] S0-001 — Repository architecture and engineering guardrails
- [x] S0-002 — Copilot agent governance and repository instructions
- [x] S0-003 — Python + uv project bootstrap
- [x] S0-004 — Code quality and test toolchain
- [x] S0-005 — Minimal GitHub Actions CI
- [ ] S0-006 — FastAPI application with `/health` and `/ready`
- [ ] S0-007 — Local dependencies and Docker Compose
