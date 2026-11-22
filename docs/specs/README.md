# AeroPulse Feature Specifications

Specifications define the observable contract for non-trivial feature delivery.

They are intentionally different from ADRs:

```text
ADR  -> why a significant technical decision exists
Spec -> what behavior a feature must deliver
```

## Status lifecycle

```text
Draft -> Approved -> Implemented
              |
              +-> Superseded
```

Only an `Approved` specification may be handed to an implementation agent.

## Required sections

Every feature spec should contain:

- status and ticket;
- problem/user outcome;
- scope;
- business/domain invariants;
- observable contract;
- acceptance criteria;
- security/data-integrity considerations;
- non-goals;
- ADR references;
- validation requirements;
- open questions (must be empty before approval).

## Change policy

If approved behavior changes during implementation:

1. stop;
2. update/review the spec first;
3. update acceptance criteria/tests;
4. continue implementation after approval.

Do not mutate the spec after implementation merely to describe whatever code happened to be
written.
