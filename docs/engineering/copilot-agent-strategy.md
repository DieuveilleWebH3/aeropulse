# AeroPulse — GitHub Copilot Agent Governance

**Ticket:** S0-002 — Copilot Agent Governance and Repository Instructions
**Status:** Proposed for Sprint 0
**Scope:** Repository-wide Copilot instructions, path-specific instructions, custom agents, reusable prompt files, issue/PR governance.
**Out of scope:** Runtime application code, CI workflow implementation, dependency bootstrap, FastAPI implementation.

---

## 1. Purpose

AeroPulse uses GitHub Copilot as an engineering accelerator, not as an autonomous source of truth.

The goals are to:

- keep agent-generated changes aligned with the architecture;
- make delegated work small, reviewable, and auditable;
- separate implementation, testing, architecture, security, and platform concerns;
- avoid duplicated or contradictory instructions;
- make human review and deterministic automation mandatory;
- support incremental delivery from GitHub issues and user stories.

---

## 2. Core Governance Rules

1. **Plan before implementation.**
2. **One ticket, one coherent scope.**
3. **Read architecture and relevant ADRs before changing code.**
4. **Do not expand scope without an explicit requirement.**
5. **Generation and validation are separate activities.**
6. **Agents never replace CI, tests, linters, type checkers, security scanners, or release automation.**
7. **Human review remains the final approval gate.**
8. **A reviewer reports first; it does not silently rewrite production code.**
9. **Business invariants are enforced in code and, where appropriate, at database level.**
10. **KISS, YAGNI, DRY, and SOLID are applied pragmatically, not ceremonially.**

---

## 3. Sources of Instructions

AeroPulse uses four distinct mechanisms.

### 3.1 Repository-wide instructions

File:

```text
.github/copilot-instructions.md
```

Contains rules that apply broadly across the repository:

- architecture;
- engineering principles;
- scope discipline;
- security baseline;
- test expectations;
- dependency management expectations;
- PR behavior.

This file must remain concise enough to be useful in every interaction.

### 3.2 Path-specific instructions

Directory:

```text
.github/instructions/
```

Files:

```text
python.instructions.md
tests.instructions.md
docs.instructions.md
workflows.instructions.md
```

These contain rules that are relevant only when files matching their glob are modified.

Do not duplicate repository-wide rules here unless the path requires a stricter interpretation.

### 3.3 Custom agents

Directory:

```text
.github/agents/
```

Custom agents define specialist behavior.

They are not separate teams and do not own independent architectures.

All agents must work within the same repository architecture.

### 3.4 Prompt files

Directory:

```text
.github/prompts/
```

Prompt files standardize recurring tasks such as:

- implementing one story;
- reviewing a change;
- creating an ADR.

Prompts are task templates, not permanent rules.

---

## 4. Agent Set

AeroPulse starts with five custom agents.

### 4.1 Architect & Documentation Agent

Primary responsibilities:

- architecture analysis;
- ADR creation/update;
- repository structure documentation;
- architecture consistency review;
- technical documentation.

Must not:

- redesign the system without a concrete requirement;
- introduce infrastructure speculatively;
- modify production implementation unless explicitly requested.

### 4.2 Backend Engineer Agent

Primary responsibilities:

- Python/FastAPI implementation;
- domain/application/infrastructure/presentation code;
- persistence and external API adapters;
- migrations when required by a story;
- implementation tests required by the story.

Must not:

- introduce a new framework or service without justification;
- bypass architecture boundaries;
- modify CI/release design unless necessary and explicitly in scope.

### 4.3 Test Engineer Agent

Primary responsibilities:

- unit tests;
- integration tests;
- contract tests;
- end-to-end tests;
- edge-case identification;
- failure-mode testing;
- test fixture quality.

Must not:

- rewrite production logic merely to make a test pass;
- assert private implementation details without a behavioral reason;
- optimize for coverage percentage instead of risk.

### 4.4 Security & Quality Reviewer Agent

Primary responsibilities:

- security review;
- authorization review;
- concurrency/race-condition review;
- reliability review;
- performance smell review;
- dependency/secret/logging review;
- architecture smell detection.

Default behavior:

- read and report;
- classify findings;
- propose remediation;
- do not edit code unless explicitly asked in a separate implementation task.

### 4.5 Platform & Release Engineer Agent

Primary responsibilities:

- uv/package management;
- Docker;
- GitHub Actions;
- dependency update mechanics;
- release process;
- infrastructure-as-code when later introduced.

Must not:

- turn deterministic build/release steps into LLM-only workflows;
- upgrade dependencies without running the project validation suite;
- add infrastructure that has not been requested by a ticket.

---

## 5. Why We Do Not Create More Agents Yet

We deliberately do **not** create separate agents for:

- unit tests;
- integration tests;
- performance optimization;
- dependency updates;
- database work;
- API work;
- ML work.

Reasons:

- responsibilities would overlap;
- handoffs would increase;
- instructions would be duplicated;
- the project is not yet large enough to justify narrower specialists.

A new agent is justified only when:

1. a recurring responsibility has a stable boundary;
2. the responsibility requires distinct instructions or tool restrictions;
3. using the existing agent set causes repeated ambiguity.

---

## 6. Agent Workflow

Normal story workflow:

```text
User Story / Technical Ticket
        |
        v
Needs & acceptance criteria
        |
        v
Implementation plan
        |
        v
Backend / Platform / Architect agent
        |
        v
Implementation + relevant tests
        |
        v
Deterministic checks
        |
        +--> lint
        +--> formatting
        +--> type checking
        +--> tests
        +--> security scanning
        |
        v
Test review (when valuable)
        |
        v
Security / quality review
        |
        v
Human review
        |
        v
Merge
```

Generation is not approval.

---

## 7. Task Sizing Rules

Good agent task:

```text
Implement US-1001 Aircraft Registration according to the attached acceptance criteria.
```

Bad agent task:

```text
Build AeroPulse.
```

A coding-agent task should normally:

- have explicit acceptance criteria;
- affect one bounded context or one infrastructure concern;
- fit in one reviewable pull request;
- have a clear validation method.

Split a task when it combines unrelated concerns such as:

- feature + dependency upgrade;
- feature + large refactor;
- API + unrelated CI changes;
- business logic + infrastructure redesign.

---

## 8. Mandatory Planning Format

Before modifying files, implementation-oriented agents must outline:

### Needs

What problem and acceptance criteria must be satisfied?

### Plan

What is the smallest coherent implementation?

### Risks

What can fail technically, functionally, operationally, or architecturally?

### Mitigations

How will those risks be prevented, detected, or constrained?

### Validation

Which tests/checks prove the ticket is complete?

If an architectural conflict is discovered, stop expansion of scope and surface the conflict.

---

## 9. Review Severity

Review findings should be classified as:

### BLOCKER

Could cause:

- security compromise;
- data corruption;
- invalid business behavior;
- broken deployment;
- unsafe destructive change.

### HIGH

Likely to cause:

- authorization errors;
- race conditions;
- unrecoverable failure behavior;
- significant architecture violation.

### MEDIUM

Important maintainability, reliability, or performance issue that should be addressed soon.

### LOW

Improvement with limited risk.

### NIT

Style/readability suggestion that is not required for correctness.

Review agents must distinguish required fixes from optional suggestions.

---

## 10. Security Review Baseline

Every relevant change should consider:

- authentication;
- authorization;
- injection;
- SSRF;
- unsafe deserialization;
- secret exposure;
- sensitive logging;
- resource exhaustion;
- unbounded retries;
- dependency vulnerabilities;
- race conditions;
- transaction boundaries;
- duplicate/replay behavior;
- unsafe file/path handling.

Not every item applies to every ticket. Review proportionally to risk.

---

## 11. Testing Governance

The implementation agent is still responsible for adding the tests required by the story.

The test engineer is an independent second pass when:

- logic is safety/business critical;
- failure modes are complex;
- concurrency is involved;
- external contracts are involved;
- a regression has occurred;
- coverage is technically present but risk coverage is doubtful.

Testing priorities:

1. business invariants;
2. failure modes;
3. boundaries;
4. state transitions;
5. idempotency/concurrency;
6. transport contract.

Coverage percentage is diagnostic information, not the goal.

---

## 12. Architecture Governance

Before introducing any of the following, evaluate whether an ADR is required:

- new database technology;
- message broker;
- new deployable service;
- new authentication mechanism;
- cross-context direct dependency;
- significant persistence pattern;
- new cloud service;
- major deployment strategy;
- breaking API/event contract.

An ADR should document:

- context;
- decision;
- alternatives;
- consequences;
- status.

---

## 13. Dependency Governance

Python dependencies will be managed with `uv`.

Rules:

- declare direct dependencies only;
- commit `uv.lock`;
- avoid unbounded speculative dependencies;
- dependency upgrades must run deterministic validation;
- security updates may be expedited but still require tests;
- a coding agent may prepare an upgrade, but CI determines whether it is acceptable.

---

## 14. CI/CD Governance

GitHub Actions owns deterministic automation.

Agents may author or maintain workflows, but must not replace:

- build;
- lint;
- type checking;
- tests;
- security scanning;
- packaging;
- tagging/release;

with natural-language-only agent actions.

Workflow changes require extra caution because they can change repository permissions and secret exposure.

---

## 15. Human Review Responsibilities

The human reviewer verifies:

- business intent;
- architectural fit;
- security significance;
- risk acceptance;
- trade-offs;
- whether an abstraction is justified;
- whether the ticket scope was respected.

Passing tests does not prove that the correct feature was built.

---

## 16. Agent Failure Modes to Avoid

### Blind propagation

One agent makes a wrong assumption and later agents treat it as truth.

Mitigation:

- reviewers verify requirements and architecture independently.

### Scope creep

The agent performs unrelated refactoring.

Mitigation:

- one-ticket scope;
- require explicit rationale for out-of-scope file changes.

### Test tailoring

Production code is distorted only to satisfy tests.

Mitigation:

- test behavior, not implementation;
- production changes need business/architecture justification.

### Premature abstraction

The agent invents generic factories/frameworks before repeated use cases exist.

Mitigation:

- YAGNI;
- prefer local explicit code first.

### Over-optimization

The agent adds caching/concurrency before measuring.

Mitigation:

- measure first;
- benchmark before/after.

### Reviewer mutation

A reviewer silently edits code and changes the meaning of the change.

Mitigation:

- security/quality reviewer is report-first.

---

## 17. Agent Selection Matrix

| Work | Primary agent | Optional second pass |
|---|---|---|
| ADR / architecture docs | Architect & Documentation | Security & Quality |
| FastAPI/domain feature | Backend Engineer | Test Engineer |
| Persistence adapter | Backend Engineer | Test Engineer |
| External API integration | Backend Engineer | Security & Quality |
| Unit/integration/contract tests | Test Engineer | Backend Engineer |
| Security review | Security & Quality | Human |
| CI workflow | Platform & Release | Security & Quality |
| uv dependency change | Platform & Release | Test Engineer |
| Docker | Platform & Release | Security & Quality |
| Release process | Platform & Release | Human |

---

## 18. Definition of Done for Agent-Generated Work

Agent-generated work is not done until:

- ticket acceptance criteria are satisfied;
- scope is respected;
- relevant tests are present;
- deterministic checks pass;
- security implications are considered;
- docs are updated where behavior/contracts changed;
- architecture deviations are documented;
- a human has reviewed the result.

---

## 19. S0-002 Acceptance Criteria

This ticket is complete when the repository contains:

- `.github/copilot-instructions.md`;
- path-specific Python/test/docs/workflow instructions;
- five custom agent profiles;
- reusable prompts for story implementation, review, and ADR creation;
- a user-story issue template;
- a pull-request template;
- this governance document.

No runtime code or CI workflow is implemented by this ticket.
