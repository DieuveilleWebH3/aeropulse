# Create an AeroPulse Architecture Decision Record

Create an ADR only for a significant, cross-cutting, costly-to-reverse, or repeatedly questioned decision.

Before writing:

1. read `docs/architecture/repository-structure.md`;
2. inspect existing ADRs to avoid duplication;
3. identify the concrete constraint/problem;
4. separate current requirements from speculative future needs.

Use this structure:

# ADR-NNN — Decision title

- Status: Proposed
- Date:
- Deciders:
- Technical area:

## Context

Describe the problem, constraints, forces, and why a decision is required now.

## Decision Drivers

List the criteria that materially affect the choice.

## Options Considered

For each serious option describe benefits, costs, and risks.

## Decision

State the selected option precisely.

## Consequences

### Positive

### Negative

### Risks and mitigations

## Rejected / Deferred Alternatives

Explain why alternatives were not selected now.

## Revisit Triggers

Define measurable conditions that would justify reconsidering the decision.

Apply KISS and YAGNI. Do not select a more complex architecture solely because it may scale better in an undefined future.
