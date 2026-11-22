---
applyTo: "docs/specs/**/*.md,docs/adr/**/*.md"
---

# Specification and ADR instructions

- Keep ADRs in `docs/adr/` and feature specifications in `docs/specs/`.
- ADRs explain significant technical decisions; specifications define observable required behavior.
- Do not duplicate an ADR inside a spec. Link to it.
- Do not encode speculative future behavior in the current spec.
- Every spec must identify scope, invariants, acceptance criteria, non-goals, risks, and validation.
- Acceptance criteria must be objectively testable.
- Security and data-integrity constraints must be explicit when relevant.
- Prefer examples that expose boundary behavior rather than implementation details.
- If a spec changes after approval, record the reason and update affected tests/docs in the same PR.
- Do not mark a spec Implemented until the implementation has passed deterministic validation.
- Apply KISS and YAGNI: the spec should define the smallest behavior required now.
