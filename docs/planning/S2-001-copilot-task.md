# Copilot Task — S2-001 Telemetry Sample Domain Model

## Recommended mode

First experiment: manually select **Spec Delivery Orchestrator**.

Give it this task:

> Deliver S2-001 from `docs/specs/S2-001-telemetry-sample-domain.md`.
> Follow `.github/copilot-instructions.md` and the Accepted ADRs under `docs/adr/`.
> Use the spec-driven orchestration sequence. Do not broaden scope.
> The orchestrator must not edit files itself: delegate architecture review, implementation,
> independent testing review, and security/quality review to the existing specialist agents.
> Stop on an unresolved architecture conflict or BLOCKER/HIGH review finding.
> At the end provide acceptance-criteria traceability and only report validation commands that
> were actually executed.

## Branch

Suggested:

```text
sprint-2/s2-001-telemetry-sample-domain
```

## Experiment evaluation

After Copilot opens/updates the PR, assess:

- Did it read ADR-001 and ADR-002?
- Did it keep all code under the Telemetry bounded context?
- Did it avoid FastAPI/SQLAlchemy/persistence/API work?
- Did it avoid adding dependencies?
- Did it implement every spec invariant without inventing freshness/range policies?
- Did the Test Engineer derive meaningful edge cases from the spec?
- Did Security & Quality report rather than silently rewrite production code?
- Did the orchestrator provide traceability rather than merely summarize agent activity?
- Did deterministic checks actually run?
- Is the PR reviewable and free of unrelated refactoring?

If orchestration creates more noise than value, keep the specialist agents and retire the
orchestrator. The experiment exists to validate the role, not justify it.
