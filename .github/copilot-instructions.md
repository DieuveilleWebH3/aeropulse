# AeroPulse — GitHub Copilot Repository Instructions

## Read first

Before making a non-trivial change:

1. read the ticket/user story and acceptance criteria;
2. read `docs/architecture/repository-structure.md`;
3. read relevant ADRs in `docs/architecture/decisions/` if they exist;
4. inspect the affected code before proposing changes;
5. outline **needs, plan, risks, mitigations, and validation**.

Do not implement beyond the ticket scope without explicitly identifying why the extra change is required.

## Engineering principles

Apply pragmatically:

- **KISS:** choose the simplest design that satisfies current requirements.
- **YAGNI:** do not add speculative services, abstractions, frameworks, or infrastructure.
- **DRY:** avoid duplicated business knowledge; do not abstract trivial duplication prematurely.
- **SOLID:** preserve clear responsibilities and dependency inversion where it adds real value.

Prefer explicit, readable code over clever code.

## Architecture

AeroPulse starts as a modular monolith with independently executable workers only when justified.

Dependency direction:

```text
Presentation -> Application -> Domain
Infrastructure -> Application/Domain contracts
```

The domain layer must not depend on:

- FastAPI;
- SQLAlchemy;
- Kafka clients;
- Redis clients;
- AWS SDKs;
- HTTP clients;
- transport-specific Pydantic schemas.

Keep FastAPI routes thin. Business rules belong in domain/application code.

Do not import another bounded context's infrastructure internals.

Do not place context-specific business logic in `shared`.

## Scope discipline

A pull request should represent one coherent ticket.

Avoid mixing:

- feature implementation and unrelated refactoring;
- dependency upgrades and feature work;
- formatting unrelated files;
- architecture redesign not required by the ticket.

If the existing architecture blocks the ticket, explain the conflict before widening the change.

## Python

Use modern typed Python.

- add type hints to public functions/methods;
- prefer small explicit functions;
- avoid broad `except Exception` unless handling/re-raising is intentional;
- never use mutable objects as default argument values;
- do not use `print()` for application logging;
- do not introduce blocking I/O inside async request paths without explicit handling;
- avoid generic `utils.py`, `helpers.py`, `manager.py`, or `common.py` dumping grounds.

Follow path-specific Python instructions for Python files.

## Tests

Tests validate behavior, invariants, contracts, and failure modes.

For production changes, add or update relevant tests.

Do not:

- change expected behavior only to make a test pass;
- over-mock the component under test;
- assert private implementation details without a behavioral reason;
- chase coverage percentage with low-value tests.

Follow path-specific test instructions under `tests/`.

## Security

For relevant changes consider:

- authentication;
- authorization;
- input validation;
- injection;
- SSRF;
- unsafe deserialization;
- secret leakage;
- sensitive logging;
- resource exhaustion;
- unbounded retries;
- race conditions;
- replay/duplicate behavior;
- transaction boundaries.

Never commit secrets, tokens, passwords, private keys, or production credentials.

## Dependencies

Python dependency management uses `uv`.

Do not manually edit lock-file internals.

Do not add a dependency when the standard library or an existing dependency is sufficient.

Any dependency addition must have a concrete use in the current ticket.

## Data integrity

Protect important invariants at the strongest practical layer.

Where appropriate use:

- database unique constraints;
- transactions;
- optimistic concurrency;
- idempotency keys.

Do not rely only on `exists()` checks for uniqueness when concurrent writes are possible.

## External systems

Treat external dependencies as unreliable.

Consider:

- timeout;
- retry eligibility;
- bounded exponential backoff;
- rate limits;
- duplicate requests;
- idempotency;
- circuit breaking when later justified.

Never retry permanent client errors indiscriminately.

## Documentation

Update documentation when changing:

- public APIs;
- event contracts;
- architecture;
- operational behavior;
- developer workflow.

Create an ADR for significant cross-cutting or hard-to-reverse decisions.

## Validation

Before declaring work complete, run the applicable deterministic checks once they exist in the repository:

- formatting;
- lint;
- type checking;
- unit tests;
- integration/contract tests where relevant;
- security checks.

If a tool is not configured yet, do not invent a command; state that validation is deferred to the ticket that introduces the tool.

## Output expectations

When completing a coding task, summarize:

1. what changed;
2. why;
3. risks/edge cases addressed;
4. tests/checks run and their results;
5. any remaining limitation or follow-up.

Never claim a test or command passed unless it was actually executed.
