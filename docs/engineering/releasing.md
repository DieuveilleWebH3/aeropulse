# AeroPulse Release Process

## Versioning

AeroPulse uses semantic version tags with a `v` prefix:

```text
v0.1.0
v0.2.0
v0.2.1
```

Package metadata uses the version without the prefix:

```toml
version = "0.1.0"
```

During the `0.x` series, the platform remains under active development and public APIs may
evolve between minor releases.

## Release prerequisites

Releases are cut from a clean, reviewed `main` branch.

Before tagging:

```bash
uv lock --check
uv run --locked --group migration alembic current
uv run --locked --group migration alembic check
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest
uv build
```

When external services are available, enable them before the full test run:

PowerShell:

```powershell
$env:AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS = "1"
```

Bash:

```bash
export AEROPULSE_RUN_EXTERNAL_SERVICE_TESTS=1
```

The focused E2E functional check is:

```bash
uv run --locked pytest -m e2e --no-cov
```

The full test suite remains the authoritative global coverage gate.

## Release checklist

1. Confirm `main` is up to date and working tree is clean.
2. Confirm `pyproject.toml` contains the intended release version.
3. Update `CHANGELOG.md`.
4. Add `docs/releases/vX.Y.Z.md`.
5. Run the complete quality/release gate.
6. Build the wheel and source distribution.
7. Create SHA-256 checksums for release assets.
8. Commit release-preparation files.
9. Push `main`.
10. Create and push the release tag.
11. Create the GitHub Release from the committed notes file.
12. Verify the release page, source archives, and attached assets.

## Tagging

Preferred when Git tag signing is configured:

```bash
git tag -s vX.Y.Z -m "AeroPulse vX.Y.Z"
git tag -v vX.Y.Z
```

Otherwise use an annotated tag:

```bash
git tag -a vX.Y.Z -m "AeroPulse vX.Y.Z"
```

Push the tag:

```bash
git push origin vX.Y.Z
```

Do not move a published release tag to a different commit.

## Build artifacts

Build:

```bash
uv build
```

Inspect the generated `dist/` directory before attaching anything to a release.

PowerShell checksum file:

```powershell
Get-FileHash dist\* -Algorithm SHA256 |
    ForEach-Object {
        "$($_.Hash.ToLower())  $(Split-Path $_.Path -Leaf)"
    } |
    Set-Content dist\SHA256SUMS.txt
```

## GitHub release

A GitHub Release is created from the exact release tag.

Using GitHub CLI:

```bash
gh release create vX.Y.Z           --title "AeroPulse vX.Y.Z — <release title>"           --notes-file docs/releases/vX.Y.Z.md           --latest
```

Release assets are optional. If attaching the package build, upload the verified wheel,
source distribution, and `SHA256SUMS.txt`.

For the first AeroPulse release:

```bash
gh release create v0.1.0           --title "AeroPulse v0.1.0 — Fleet & Asset Management Foundation"           --notes-file docs/releases/v0.1.0.md           --latest
```

## Post-release verification

Confirm:

- the release targets the expected commit;
- the tag is visible;
- the release is marked latest;
- release notes render correctly;
- source ZIP/tarball are available;
- optional wheel/sdist checksums match;
- `CHANGELOG.md` contains the released version.

Development then resumes with the next unreleased milestone.
