# AeroPulse — Code Quality and Testing Toolchain

**Ticket:** S0-004 — Code quality and test toolchain
**Status:** Accepted for Sprint 0

## 1. Purpose

This ticket introduces deterministic developer-side quality gates before application code is added.

The toolchain covers four complementary concerns:

- linting and formatting;
- static type checking;
- automated testing and coverage;
- local Git hook orchestration.

It deliberately does not introduce application runtime dependencies.

## 2. Tool Selection

| Concern | Tool | Initial compatibility range |
|---|---|---|
| Linting + formatting | Ruff | `>=0.17.3,<0.18` |
| Static typing | mypy | `>=2.4.1,<2.5` |
| Testing | pytest | `>=9.2.0,<10` |
| Coverage | pytest-cov | `>=7.1.0,<8` |
| Local hooks | pre-commit | `>=4.7.0,<5` |

The committed `uv.lock` remains the exact reproducibility mechanism. Version ranges in
`pyproject.toml` define the allowed compatibility window for deliberate future lock updates.

## 3. Why These Tools?

### Ruff

Ruff gives AeroPulse one fast tool for both linting and formatting.

The selected lint families are intentionally curated:

- `E4`, `E7`, `E9`: high-value pycodestyle errors;
- `F`: Pyflakes correctness checks;
- `I`: import ordering;
- `UP`: modern Python upgrades;
- `B`: bug-prone constructs;
- `SIM`: unnecessary complexity;
- `RUF`: Ruff-specific correctness/quality rules.

We do not enable `ALL`.

Enabling every available rule would create noise, conflicting style opinions, and maintenance work
unrelated to product risk.

Ruff targets Python 3.14 explicitly.

### mypy

AeroPulse starts with strict typing while the codebase is small.

This is cheaper than gradually retrofitting type discipline after domain, persistence, API, and event
contracts have spread.

`strict = true` is a baseline for AeroPulse-owned code, not a promise that every third-party library
will always be perfectly typed.

If a future dependency lacks useful type information, prefer the narrowest targeted override instead
of weakening typing globally.

### pytest

pytest owns executable behavior tests.

Strict marker/config parsing is enabled so misspelled configuration and markers fail rather than
silently changing test behavior.

`xfail` is strict: an unexpectedly passing test is treated as a signal that the test expectation
needs review.

### pytest-cov

Coverage is a risk indicator, not the objective.

A global floor of **90%** is used because AeroPulse is intentionally starting from an empty codebase
and can establish strong test discipline early.

The project should still prefer:

1. business invariants;
2. failure paths;
3. state transitions;
4. concurrency/idempotency behavior;
5. integration contracts;

over superficial line execution.

100% coverage is not a project goal.

### pre-commit

pre-commit orchestrates local feedback but does not replace CI.

The `pre-commit` Git stage performs fast, potentially auto-fixing checks:

- Ruff lint;
- Ruff format.

The `pre-push` stage performs slower non-mutating validation:

- mypy;
- pytest.

Local hooks invoke the project-locked tools through `uv run --locked`, so they do not maintain
independent Python tool environments or versions.

## 4. Developer Setup

After applying S0-004, resolve and commit the dependency lock:

```bash
uv lock
uv sync --locked
```

Install Git hooks:

```bash
uv run --locked pre-commit install
```

Because `default_install_hook_types` contains both `pre-commit` and `pre-push`, this installs both
hook types.

## 5. Canonical Validation Commands

### Lint

```bash
uv run --locked ruff check .
```

### Verify formatting

```bash
uv run --locked ruff format --check .
```

### Apply formatting

```bash
uv run --locked ruff format .
```

### Type checking

```bash
uv run --locked mypy
```

### Tests + coverage

```bash
uv run --locked pytest
```

### Run all pre-commit-stage hooks manually

```bash
uv run --locked pre-commit run --all-files
```

### Run pre-push hooks manually

```bash
uv run --locked pre-commit run --all-files --hook-stage pre-push
```


## Deprecation Warning Policy

Known framework deprecations should not remain permanently visible in the test suite.

AeroPulse currently promotes:

```text
starlette.exceptions.StarletteDeprecationWarning
```

to a pytest error.

This protects the `TestClient` stack from silently falling back to deprecated `httpx` behavior.

Do not globally convert every Python warning to an error without review. Warning escalation should
remain targeted so third-party noise does not make the suite unnecessarily brittle.

## 6. Test Layout

The architecture remains:

```text
tests/
├── unit/
├── integration/
├── contract/
└── e2e/
```

S0-004 creates only:

```text
tests/unit/test_package.py
```

because there is no database, external contract, or multi-component runtime to integrate yet.

Creating empty integration/contract/e2e suites now would add structure without behavior.

## 7. First Smoke Test

The initial test proves two things:

1. the installed `aeropulse` package is importable;
2. installed distribution metadata exposes version `0.1.0`.

The second assertion is important for a `src/` layout: it verifies the project is installed into the
environment instead of tests accidentally importing code from the repository root.

## 8. Coverage Policy

Initial threshold:

```text
90%
```

This is a repository-wide guardrail, not a substitute for risk-based tests.

Do not:

- add `# pragma: no cover` merely to satisfy the percentage;
- write assertions with no behavioral value;
- exclude difficult business logic from coverage;
- test private implementation details solely to increase the number.

Legitimate exclusions should be rare and explained.

## 9. Formatting Policy

Ruff is the only Python formatter.

Do not add Black, isort, autopep8, or another overlapping formatter unless an explicit migration
decision replaces Ruff.

Line length:

```text
100
```

This is intentionally readable without aggressively wrapping ordinary typed Python signatures.

## 10. Type-Checking Policy

AeroPulse-owned production and test code are both checked.

Do not solve typing errors by defaulting to:

```python
Any
```

or broad `# type: ignore`.

When an ignore is genuinely required:

- narrow it to the exact error code where possible;
- explain the third-party/tool limitation when non-obvious.

## 11. Pre-commit Policy

Fast auto-fixes are acceptable before commit.

Expensive test/type checks occur at pre-push.

Developers may run commands directly at any time; hooks are convenience guardrails, not the source
of truth.

CI, introduced in S0-005, will execute the non-mutating canonical checks again in a clean
environment.

## 12. Risks and Mitigations

### Excessively strict lint rules

**Risk:** engineers spend time satisfying subjective rules.

**Mitigation:** curated Ruff rule families; no `ALL`.

### Type checker friction with external libraries

**Risk:** global weakening of mypy to accommodate one dependency.

**Mitigation:** retain strict project defaults and introduce narrow per-module exceptions only when
evidence requires them.

### Coverage gaming

**Risk:** tests execute lines without proving behavior.

**Mitigation:** retain the 90% floor but review tests based on business/failure scenarios.

### Slow local commits

**Risk:** developers bypass hooks.

**Mitigation:** commit stage only runs Ruff; mypy and tests run at pre-push.

### Tool version drift

**Risk:** local/CI results disagree.

**Mitigation:** tools are project dependencies, resolved in committed `uv.lock`, and invoked via
`uv run --locked`.

### Mutating CI

**Risk:** a formatting/lint job silently changes code rather than reporting a failure.

**Mitigation:** CI will use `ruff check .` and `ruff format --check .`; auto-fixing stays local.

## 13. Non-goals

S0-004 does not add:

- GitHub Actions;
- Bandit/pip-audit/CodeQL;
- FastAPI;
- async test plugins;
- testcontainers;
- Docker;
- database fixtures;
- integration infrastructure.

Those tools are introduced only by tickets with concrete requirements.

## 14. Definition of Done

S0-004 is complete when, using the target Python/uv toolchain:

```bash
uv lock
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
uv run --locked pre-commit run --all-files
uv run --locked pre-commit run --all-files --hook-stage pre-push
```

all succeed and the regenerated `uv.lock` is committed with the ticket.
