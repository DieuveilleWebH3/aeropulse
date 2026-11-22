# ADR-001 — Adopt spec-driven development for scoped feature delivery

- Status: Accepted
- Date: 2026-11-22
- Deciders: AeroPulse maintainers
- Technical area: Engineering process / AI-assisted development

## Context

AeroPulse now has a stable Sprint 1 Fleet foundation and multiple GitHub Copilot specialist
agents. Feature work is becoming more cross-layer and the next phase introduces telemetry and
PHM concepts whose contracts must remain clear before implementation.

User stories alone capture intent but can leave technical behavior implicit. Coding agents may
then fill gaps differently, expand scope, or optimize for an implementation rather than the
required behavior.

We need a lightweight contract between product intent, architecture decisions, implementation,
tests, and AI-assisted delivery.

## Decision Drivers

- make agent-generated work bounded and reviewable;
- prevent requirements from being invented during implementation;
- preserve human control over behavior and architecture;
- keep ADR rationale separate from feature behavior;
- maintain traceability from acceptance criteria to tests;
- avoid a heavyweight specification process for trivial changes;
- preserve KISS, YAGNI, DRY, SOLID, and security review.

## Options Considered

### Option A — Issue-only development

Keep all requirements in GitHub issues and allow implementation agents to infer technical
details.

Benefits:

- minimal process;
- low documentation overhead.

Costs/risks:

- ambiguous behavior becomes implementation-dependent;
- harder independent testing;
- increased agent scope drift;
- design rationale and behavioral requirements become mixed.

### Option B — Spec-driven development for scoped features

Use a versioned Markdown specification for non-trivial feature stories and keep ADRs for
significant technical decisions.

Benefits:

- explicit observable behavior before code;
- independent implementation/test review against the same contract;
- better AI-agent boundaries;
- lightweight and repository-native.

Costs/risks:

- additional document to maintain;
- poor specs can become bureaucracy if written at implementation-detail level.

### Option C — Full formal specification/model-driven process

Introduce schemas/models and generated implementations as the primary development mechanism.

Benefits:

- strong machine-readable contracts.

Costs/risks:

- disproportionate complexity at the current project stage;
- new tooling and maintenance burden;
- would violate YAGNI without evidence that Markdown specs are insufficient.

## Decision

Adopt **Option B**.

Non-trivial feature delivery follows:

```text
Issue / user outcome
    -> Approved specification
    -> ADR gate (only when a significant decision exists)
    -> implementation
    -> independent tests/review
    -> deterministic validation
    -> human review
```

Specifications live in `docs/specs/`.

ADRs live in `docs/adr/`.

Source-of-truth responsibilities are:

```text
Issue -> why the user/business needs the change
ADR   -> why a significant technical decision was chosen
Spec  -> what observable behavior the feature must deliver
Code  -> how the approved behavior is implemented
Tests -> executable evidence of the approved behavior
```

A spec must not silently override an Accepted ADR. Code must not silently redefine a spec.

Specs are required for new user-visible features and non-trivial cross-layer behavior. Tiny
refactors, documentation corrections, dependency maintenance, and bug fixes whose intended
behavior is already unambiguous do not automatically require a new spec.

## Consequences

### Positive

- agents receive a smaller, explicit behavioral contract;
- Test Engineer can derive tests independently from the implementation;
- architecture decisions remain separated from feature details;
- PR reviews can trace acceptance criteria directly to evidence;
- scope creep becomes easier to detect.

### Negative

- maintainers must keep the spec synchronized when approved behavior changes;
- weak or over-detailed specs can constrain implementation unnecessarily.

### Risks and mitigations

**Risk:** specifications turn into design-by-document bureaucracy.

**Mitigation:** specify observable behavior/invariants/non-goals, not internal class diagrams
unless architecture requires them.

**Risk:** agents implement a Draft spec.

**Mitigation:** implementation prompts and orchestrator require `Status: Approved`.

**Risk:** implementation and spec diverge.

**Mitigation:** PR/agent traceability explicitly maps acceptance criteria to tests/evidence.

## Rejected / Deferred Alternatives

Formal executable specification/code generation is deferred until concrete duplication or
contract-management pain demonstrates a need.

## Revisit Triggers

Reconsider this decision if:

- Markdown specs repeatedly become inconsistent with code despite review;
- multiple consumers require machine-readable contracts;
- event/API schemas become complex enough to justify generated contracts;
- spec maintenance cost exceeds demonstrated delivery/review benefit.
