# AeroPulse

**Predictive Maintenance & Fleet Health Monitoring Platform**

AeroPulse is an engineering portfolio project demonstrating the design of a production-oriented predictive-maintenance platform with Python, FastAPI, event-driven processing, data engineering, observability, security, testing, and cloud infrastructure.

> Current status: **Sprint 0 — Foundation**

## Current bootstrap

The repository currently establishes the Python package/toolchain foundation. Application runtime dependencies such as FastAPI are intentionally introduced in later tickets.

### Prerequisites

- `uv >= 0.13.6, < 0.14`
- CPython `3.14.10` (uv can install it)

### Setup

```bash
uv python install 3.14.10
uv sync --locked
```

### Verify the package

```bash
uv run --locked python -c "import aeropulse; print(aeropulse.__name__)"
```

Expected:

```text
aeropulse
```

### Build

```bash
uv build
```

## Engineering documentation

- [Repository architecture](docs/architecture/repository-structure.md)
- [Copilot agent strategy](docs/engineering/copilot-agent-strategy.md)
- [Python toolchain](docs/engineering/python-toolchain.md)

## Foundation roadmap

- [x] S0-001 — Repository architecture and engineering guardrails
- [x] S0-002 — Copilot agent governance and repository instructions
- [x] S0-003 — Python + uv project bootstrap
- [ ] S0-004 — Code quality and test toolchain
- [ ] S0-005 — Minimal GitHub Actions CI
- [ ] S0-006 — FastAPI application with `/health` and `/ready`
- [ ] S0-007 — Local dependencies and Docker Compose
