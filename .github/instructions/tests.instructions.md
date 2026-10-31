---
applyTo: "tests/**/*.py"
---

# Test-specific instructions

Tests must validate observable behavior and risk.

## Test selection

Use the smallest suitable test level:

- unit: pure domain/application behavior;
- integration: real infrastructure boundary;
- contract: external API/event contract;
- e2e: small number of critical cross-component flows.

## Required thinking

For the behavior under test, consider:

- happy path;
- invalid input;
- boundary values;
- duplicate/idempotent input;
- state transition violations;
- concurrency conflicts where relevant;
- dependency timeout/failure;
- authorization failure where relevant.

## Test quality

- Use descriptive behavioral test names.
- Keep tests deterministic.
- Avoid sleeps for synchronization.
- Freeze/control time instead of relying on wall-clock timing.
- Prefer fixtures/builders that express intent.
- Keep fixture scope as narrow as practical.
- Do not mock the subject under test.
- Avoid mocking infrastructure when the infrastructure contract is exactly what the test needs to validate.
- Do not assert implementation details unless they are part of the contract.
- A regression test should fail before the fix and pass after it.
- Coverage is not a substitute for scenario quality.
