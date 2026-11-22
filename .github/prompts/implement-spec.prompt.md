# Implement one approved AeroPulse specification

Implement exactly one approved specification referenced by the user.

Before editing:

1. read `.github/copilot-instructions.md`;
2. read the linked GitHub issue/ticket;
3. read the specification under `docs/specs/`;
4. confirm its status is `Approved`;
5. read relevant ADRs under `docs/adr/`;
6. inspect affected code and existing tests.

If the spec is ambiguous, incomplete, or conflicts with an accepted ADR/current public
contract, stop and report the conflict before implementation.

Provide first:

## Needs

Restate the user outcome and specification contract.

## Acceptance traceability

List every acceptance criterion and the intended evidence for it.

## Plan

Give the smallest implementation sequence.

## Risks

Consider business invariants, data integrity, security, concurrency, reliability,
compatibility, resource exhaustion, and architecture boundaries where applicable.

## Mitigations

State how code/tests constrain those risks.

## ADR impact

State which ADRs apply and whether a new significant decision is required.

## Implementation

Implement only the approved scope.

Rules:

- preserve Presentation -> Application -> Domain dependency direction;
- keep infrastructure behind inward-facing contracts;
- apply KISS, YAGNI, DRY, and SOLID pragmatically;
- do not add speculative abstractions or dependencies;
- do not silently change the spec to match the implementation;
- do not refactor unrelated files;
- add risk-based tests that prove the acceptance criteria;
- preserve security and data integrity at the strongest practical layer.

## Validation

Run all applicable deterministic checks configured by the repository.

Finish with:

- acceptance-criteria traceability;
- files changed;
- tests/checks actually executed and results;
- security/architecture considerations;
- unresolved risks or follow-ups.

Never claim a command passed unless it actually ran.
