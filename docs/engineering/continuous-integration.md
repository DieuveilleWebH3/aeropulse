# AeroPulse — Continuous Integration

**Ticket:** S0-005 — Minimal GitHub Actions CI
**Status:** Accepted for Sprint 0

## 1. Purpose

S0-005 makes the deterministic quality gates introduced in S0-004 executable in a clean GitHub
Actions environment.

The CI workflow is intentionally small.

It answers one question:

> Is this revision safe enough, from the currently automated quality perspective, to be reviewed and
> merged?

It does not deploy, release, mutate source files, or provision infrastructure.

## 2. Workflow

File:

```text
.github/workflows/ci.yml
```

Triggers:

- every pull request;
- pushes to `main`;
- manual `workflow_dispatch`.

The workflow contains one stable required job:

```text
CI / quality
```

Starting with S0-007, that job also provisions PostgreSQL and Redis service containers so the
runtime dependency adapters are validated against real services.

The job performs, in order:

```text
start PostgreSQL + Redis service containers
-> checkout
-> install uv
-> install Python
-> validate uv.lock
-> sync locked dependencies
-> verify Python version
-> Ruff lint
-> Ruff format check
-> mypy
-> pytest + coverage + live dependency integration
```

## 3. Why One Job?

S0-005 deliberately uses one `quality` job rather than separate lint/type/test jobs.

Advantages at the current project size:

- no repeated checkout/environment bootstrap;
- one stable branch-protection check;
- simpler workflow ownership;
- fewer moving pieces;
- infrastructure integration is validated in the same required gate.

This is a KISS decision.

Split the workflow into parallel jobs only when measured runtime, fault isolation, permissions, or
different runtime requirements justify the additional duplication.

## 4. Least-Privilege Permissions

The workflow declares:

```yaml
permissions:
  contents: read
```

The validation workflow does not require write access.

It must not gain permissions such as:

```text
contents: write
pull-requests: write
packages: write
id-token: write
```

unless a later ticket introduces a concrete action that requires them.

Deployment and release privileges belong in separate workflows.

## 5. Third-Party Action Pinning

Third-party actions are pinned to immutable full commit SHAs:

```text
actions/checkout
astral-sh/setup-uv
```

A human-readable release comment is kept beside each SHA.

This reduces the risk of a mutable tag unexpectedly changing executable CI code.

Updating an action should be reviewed like any other dependency update.

## 6. Runner Pinning

The validation job runs on:

```yaml
runs-on: ubuntu-24.04
```

The workflow deliberately does not use `ubuntu-latest`.

`ubuntu-latest` is a moving alias and can migrate to a newer runner image over time. Pinning the
Ubuntu image family reduces environment drift while still receiving GitHub's maintained runner image
updates within that family.

If AeroPulse later requires a newer runner image, update it through a reviewed tooling ticket.

## 7. Checkout Security

Checkout uses:

```yaml
persist-credentials: false
```

The quality job does not need to push commits or tags, so persisted GitHub credentials are
unnecessary.

The workflow uses the normal `pull_request` trigger, not `pull_request_target`.

Do not replace it with `pull_request_target` merely to obtain secrets or elevated permissions for
untrusted pull-request code.

## 8. uv and Python Reproducibility

CI pins:

```text
uv 0.13.6
CPython 3.14.10
```

The repository also declares its supported uv/Python ranges in project configuration.

CI executes:

```bash
uv lock --check
```

before installing dependencies.

This detects a `pyproject.toml` change whose corresponding lockfile was not committed.

Dependencies are then installed with:

```bash
uv sync --locked --group dev
```

No dependency resolution is permitted to silently modify `uv.lock`.

## 9. Cache Strategy

`astral-sh/setup-uv` manages the uv cache.

The cache key is tied to:

```text
uv.lock
```

through:

```yaml
cache-dependency-glob: "uv.lock"
```

This cache accelerates downloads; it does not replace the lockfile.

Correctness must never depend on cache contents.

If cache behavior becomes suspicious, CI must still work with caching disabled.

## 10. Runtime Service Containers

S0-007 provisions:

```text
PostgreSQL 18.6
Redis 8.10.3
```

as GitHub Actions service containers.

The CI environment sets:

```text
AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1
```

so the live runtime-dependency integration test executes.

These services have development/CI-only credentials and no production secrets.

Their health checks must succeed before the quality steps execute.


### Ephemeral PostgreSQL authentication

The CI PostgreSQL service intentionally does not use a stored password.

It uses:

```yaml
POSTGRES_HOST_AUTH_METHOD: trust
```

only inside the disposable GitHub-hosted runner. The corresponding CI database URL therefore
contains no password.

This is a CI-only exception. PostgreSQL `trust` authentication must not be copied into local,
staging, or production deployment configuration.

Why this approach is preferred here:

- the database contains only disposable test data;
- no long-lived credential exists to leak;
- ordinary pull requests do not depend on GitHub Actions secrets;
- fork pull requests remain testable;
- secret scanners do not need to ignore a synthetic CI password.

Real deployment/runtime secrets must use an appropriate secret manager rather than this pattern.

## 11. Non-Mutating CI

CI never runs:

```bash
ruff check --fix
ruff format
```

Instead it runs:

```bash
ruff check .
ruff format --check .
```

Source mutation belongs to the developer/agent workspace before a PR is submitted.

CI reports drift; it does not rewrite the branch.

## 12. Test Gate

The pytest command inherits S0-004's repository configuration, including:

- strict pytest configuration;
- strict markers;
- branch coverage;
- 90% coverage floor.

Therefore:

```bash
uv run --locked pytest
```

is itself the coverage gate.

There is no second independently configured coverage command.

## 13. Concurrency

The workflow uses:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

When a developer pushes several revisions to the same PR/branch, stale CI work is cancelled.

This reduces wasted runner capacity and avoids reviewers waiting on obsolete commits.

Release/deployment workflows may require different concurrency semantics later.

## 14. Timeout

The quality job has:

```yaml
timeout-minutes: 15
```

The current repository should complete far below that.

A timeout prevents a hung tool or network operation from consuming a runner indefinitely.

If ordinary CI approaches this limit, investigate the cause rather than immediately increasing the
timeout.

## 15. Branch Protection / Ruleset

After S0-005 is merged and has run successfully, configure the repository's `main` ruleset/branch
protection to require the CI status check.

Recommended initial protections:

- require a pull request before merging;
- require the `CI / quality` status check;
- require the branch to be up to date before merge if the team's merge strategy needs it;
- block force pushes to `main`;
- block deletion of `main`.

Do not require a check before it has run at least once, because GitHub needs to know the check name.

Human review remains required even when CI passes.

## 16. Why Security Scanning Is Not Added Here

S0-005 is the **minimal CI** ticket.

It does not add:

- CodeQL;
- dependency audit tooling;
- secret scanners;
- container scanning;
- SAST orchestration.

Those controls require their own dependency/permission/configuration decisions.

They should be introduced deliberately rather than hidden inside the first workflow.

The existing CI still reduces security risk through:

- immutable action pinning;
- read-only token permissions;
- no persisted checkout credentials;
- locked dependencies;
- no secrets;
- no `pull_request_target`.

## 17. Failure Interpretation

### `uv lock --check` fails

Likely cause:

```text
pyproject.toml changed but uv.lock was not regenerated
```

Fix locally:

```bash
uv lock
uv sync --locked
```

Review the lockfile diff and commit it.

### Ruff lint fails

Fix locally:

```bash
uv run --locked ruff check --fix .
```

Then review the changes.

### Ruff format check fails

Fix locally:

```bash
uv run --locked ruff format .
```

### mypy fails

Fix the type/design issue.

Do not globally weaken strictness for a local incompatibility.

### pytest fails

Fix the behavior or the test based on the ticket contract.

Do not reduce the coverage floor merely to make CI green.

## 18. Local CI Parity

Before pushing, a developer can reproduce the CI quality commands with:

```bash
uv lock --check
uv sync --locked --group dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
```

The ordinary local suite skips the live PostgreSQL/Redis test unless
`AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1` is set. CI always enables it.

Local Git hooks remain useful fast feedback, but GitHub Actions is the merge gate.

## 19. Future Evolution Triggers

Consider splitting jobs when:

- CI duration becomes materially slow;
- tests require PostgreSQL/Kafka/service containers while lint does not;
- different Python/runtime matrices become necessary;
- integration tests require credentials or isolated permissions;
- expensive suites should run conditionally.

Consider adding a Python-version matrix when AeroPulse officially supports more than one Python minor.

Do not add a matrix merely to demonstrate GitHub Actions knowledge.

## 20. Definition of Done

S0-005 is complete when:

1. `.github/workflows/ci.yml` is committed;
2. the workflow runs on a pull request;
3. `CI / quality` passes;
4. locked dependency validation passes;
5. Ruff lint/format validation passes;
6. mypy passes;
7. pytest and the coverage threshold pass;
8. no workflow write permission is required;
9. branch protection/ruleset can use `CI / quality` as a required check.
