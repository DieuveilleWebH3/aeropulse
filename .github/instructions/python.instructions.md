---
applyTo: "**/*.py"
---

# Python-specific instructions

- Keep domain code framework-independent.
- Use type hints for public interfaces and non-trivial internal APIs.
- Prefer `collections.abc` protocol types for parameters when appropriate.
- Prefer composition over deep inheritance.
- Prefer explicit dataclasses/value objects for domain concepts when they improve invariants.
- Raise specific exceptions with domain/application meaning.
- Preserve exception context when translating infrastructure errors.
- Avoid boolean parameters that radically change function behavior; prefer explicit operations.
- Avoid hidden global state and import-time side effects.
- Keep async boundaries deliberate: use `async` for actual asynchronous I/O, not by default.
- Do not perform blocking network/database/file operations directly in an async request path.
- Do not add a framework abstraction until a concrete repeated need exists.
- Prefer domain names such as `AircraftRegistration` over generic names such as `DataManager`.
- New Python code must be compatible with the Python version declared in `.python-version` once that file exists.
- Use the project tooling declared in `pyproject.toml` once Sprint 0 configures it.
