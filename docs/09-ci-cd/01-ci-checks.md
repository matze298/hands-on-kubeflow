# CI Checks

This page creates the baseline CI workflow.

## What You Will Build

You will create:

```text
.github/workflows/ci.yaml
ci/README.md
```

The workflow runs:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
uv run mkdocs build --strict
```

## Why This Matters

Container builds and pipeline compilation should not happen before basic checks pass.

The order should be:

```text
format
  ↓
lint
  ↓
type check
  ↓
tests
  ↓
docs build
  ↓
images / pipeline artifacts
```

## Create the CI Folder

```bash
mkdir -p .github/workflows
mkdir -p ci
```

## Create `ci/README.md`

Create `ci/README.md`:

```markdown
# CI/CD

This folder contains helper scripts and documentation for CI/CD workflows.

The CI/CD expansion keeps the repository docs-first:

- implementation files are created while following the tutorial
- workflows call the same `uv` commands used locally
- pipeline compilation is reproducible
- image tags are explicit
- promotion is represented as Git-tracked state

## Core Local Check

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
uv run mkdocs build --strict
```
```

## Create `.github/workflows/ci.yaml`

```yaml
name: CI

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  checks:
    name: Python and docs checks
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Sync dependencies
        run: uv sync --all-extras --dev

      - name: Check formatting
        run: uv run ruff format --check .

      - name: Lint
        run: uv run ruff check .

      - name: Type check
        run: uv run ty check

      - name: Test
        run: uv run pytest

      - name: Build docs
        run: uv run mkdocs build --strict
```

## Why Use the Same Commands as Local?

The CI workflow should not invent a separate validation path.

If the local check is:

```bash
uv run pytest
```

then CI should also use:

```bash
uv run pytest
```

This keeps the tutorial honest.

## Optional Local Helper

If the repo uses `Makefile`, add:

```makefile
.PHONY: check
check:
	uv run ruff format --check .
	uv run ruff check .
	uv run ty check
	uv run pytest
	uv run mkdocs build --strict
```

If the repo uses another existing convention, keep that convention instead.

## Common Problems

### CI fails but local passes

Check Python version and dependency lock state.

Run locally:

```bash
uv sync --all-extras --dev
uv run mkdocs build --strict
```

### `mkdocs build --strict` fails on links

This is good. Broken tutorial links should fail CI.

### `ty` changes behavior

Pin the version in `uv.lock` and update intentionally.

## Acceptance Criteria

You are done when:

- `.github/workflows/ci.yaml` exists
- CI runs on pull requests
- CI runs on pushes to `main`
- `uv` is used in CI
- formatting, linting, type checks, tests, and docs build run automatically

## References

- [GitHub Actions workflow syntax](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
- [uv GitHub Actions integration](https://docs.astral.sh/uv/guides/integration/github/)
- [MkDocs command line](https://www.mkdocs.org/user-guide/cli/)

## Next Step

Continue with [Build Images](02-build-images.md).
