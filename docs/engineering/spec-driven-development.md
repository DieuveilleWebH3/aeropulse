# AeroPulse Spec-Driven Development

AeroPulse uses a lightweight Spec-Driven Development (SDD) workflow for non-trivial feature
stories.

## Workflow

```text
GitHub issue / user outcome
         |
         v
   Draft specification
         |
         v
   Human approval
         |
         v
   Architecture / ADR gate
         |
         v
    Implementation
         |
         +----> independent test review
         |
         +----> security / quality review
         |
         v
   deterministic checks
         |
         v
      human review
         |
         v
        merge
```

## Why

The purpose is not to produce more documentation. The purpose is to keep behavior stable while
humans and coding agents work independently.

A useful spec answers:

- what must be true?
- what is explicitly not being built?
- what boundary behavior matters?
- what security/data-integrity constraints matter?
- what objective evidence proves completion?

It should generally avoid prescribing class hierarchies or internal abstractions.

## Spec readiness gate

Implementation starts only when:

- status is `Approved`;
- acceptance criteria are testable;
- non-goals are explicit;
- open questions are empty;
- significant architecture decisions are covered by an Accepted ADR or explicitly identified
  for resolution.

## Traceability

Agent/human review should be able to construct:

| Acceptance criterion | Implementation | Test/evidence | Result |
|---|---|---|---|

Missing evidence means the story is not complete even if code compiles.

## Security

Security is part of the spec when behavior creates a relevant attack/data-integrity surface.

Do not add generic security machinery to every story. Apply proportionate controls for the
concrete risk, then use the Security & Quality Reviewer as an independent review pass.

## YAGNI / KISS rule

A spec may explicitly defer behavior. Deferred behavior must remain deferred unless a new
requirement is approved.

Agents must not interpret "future-ready" as permission to introduce:

- message brokers;
- new databases;
- microservices;
- generic plugin systems;
- caching;
- retries;
- batching;
- cloud resources;

unless the current spec/ADR requires them.
