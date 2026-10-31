---
applyTo: ".github/workflows/**/*.yml,.github/workflows/**/*.yaml"
---

# GitHub Actions workflow instructions

GitHub Actions is deterministic automation and must remain auditable.

- Apply least-privilege `permissions`.
- Do not expose secrets to untrusted pull-request code.
- Pin third-party actions to a stable major/version policy selected by the project; prefer immutable pinning for security-sensitive production workflows when established.
- Do not print secrets or sensitive environment values.
- Use `uv` for Python environment/dependency operations once configured.
- CI should fail on lint/type/test/security failures rather than masking them.
- Avoid `continue-on-error` for required quality gates.
- Avoid unnecessary write permissions.
- Do not add deployment/release permissions to ordinary CI jobs.
- Separate validation from release/deployment concerns.
- Cache only when correctness is preserved.
- Keep workflows understandable; extract reusable workflows only after repetition justifies it.
- Any workflow change that alters permissions, secrets, release, or deployment behavior requires explicit review.
