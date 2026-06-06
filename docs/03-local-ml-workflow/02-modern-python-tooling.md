# Modern Python Tooling

This page sets up the Python tooling for the local ML workflow.

The tutorial uses current tooling by default:

- `uv` for dependency management and local commands
- `ruff` for linting and formatting
- `ty` for type checking
- `pytest` for tests
- `mkdocs-material` for documentation
- `marimo` for optional interactive exploration

## What You Will Build

You will configure a Python project that supports:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run ty check
```

## Why This Matters

Kubeflow introduces enough complexity on its own.

Before running code in containers or Kubernetes, we want fast local checks:

```text
format
  ↓
lint
  ↓
type check
  ↓
test
  ↓
container build
  ↓
pipeline run
```

Do not debug in Kubernetes what you could have caught locally.

## Initialize or Update the Project

If the repository does not yet have `pyproject.toml`:

```bash
uv init --package kubeflow-by-doing
```

If it already exists, update it intentionally instead of replacing repo conventions.

## Add Dependencies

Add runtime dependencies:

```bash
uv add kfp torch typer rich
```

Add development dependencies:

```bash
uv add --dev pytest ruff ty mkdocs-material marimo
```

!!! note

    Keep dependencies minimal. The ML task is intentionally small; Kubeflow and Kubernetes are the learning targets.

## Example Project Files

Treat these as the shape of the files this tutorial expects, not as a verbatim dump of every repository.
If your clone already has equivalent config, keep the repo's actual values and adapt only what needs to change for the chapter.

`pyproject.toml` example:

```toml
[project]
name = "kubeflow-hands-on"
version = "0.1.0"
description = "Local-first Kubeflow tutorial project."
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    "kfp>=2.16.1",
    "rich>=15.0.0",
    "torch>=2.12.0",
    "typer>=0.26.7",
]

[project.scripts]
kbd = "kubeflow_by_doing.cli:app"

[dependency-groups]
docs = [
    "mkdocs-material>=9.7.6",
]

dev = [
    "marimo>=0.23.9",
    "prek>=0.4.1",
    "pytest>=9.0.3",
    "ruff>=0.15.13",
    "ty>=0.0.38",
    "typer",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/kubeflow_by_doing"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

`ruff.toml` example:

```toml
target-version = "py314"
line-length = 120
preview = true
fix = true

[lint]
select = ["ALL"]

ignore = [
    "COM812", # Recommended ignore from ruff-format
    "CPY001", # No copyright added yet
    "D203",   # One blank line before class (Google prefers no extra line)
    "D213",   # Multi-line docstring summary on first line
    "E501",   # Line length handled by formatter guidance
    "FIX002", # Allow ToDo comments
    "G004", # Allow f-strings in logs
    "TRY301", # Allow to raise Exceptions within try blocks
]

pydocstyle.convention = "google"

[lint.per-file-ignores]
"setup.py" = ["PLC0415", "S404", "S603"]

[format]
preview = true
```

The exact Ruff ignore list is a repository preference, not a universal standard. If your team prefers a different linting balance, adjust the ignore list intentionally and keep the decision documented the same way you would for `ty` rules.

The repo uses `prek` for pre-commit hooks. The bootstrap script installs them with:

```bash
uv run prek install --prepare-hooks
```

The backing config lives in `prek.toml`, which keeps the generic pre-commit hooks and the repo-local `ruff` and `ty` hooks together.

## Verify the Environment

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

At this point, some checks may fail because the source and test files do not exist yet. That is acceptable while building the chapter. By the end, they should pass or have a documented temporary exception.

## Optional Local Check Command

If the repo already uses a `Makefile`, a small `check` target is acceptable:

```makefile
.PHONY: check
check:
	uv run ruff format --check .
	uv run ruff check .
	uv run ty check
	uv run pytest
```

If the repo does not already use a `Makefile`, do not add one just for this chapter. Running the `uv run` commands directly is enough.

## Common Problems

### `ty` is noisy or changes behavior

`ty` is modern tooling. If output changes between versions, pin the version and document the exception rather than replacing it with older defaults.

### PyTorch installation is large

That is expected. For local NVIDIA workflows, make sure your PyTorch build matches your CUDA environment.

### `pytest` finds no tests

Expected before test files are created. It should pass by the end of the chapter.

## Acceptance Criteria

You are done when:

- `pyproject.toml` exists
- runtime and dev dependencies are managed by `uv`
- `uv sync` succeeds
- `uv run ruff check .` runs
- `uv run ruff format --check .` runs
- `uv run ty check` runs
- `uv run pytest` runs
- `kfp` is available to the local project

## References

- [uv documentation](https://docs.astral.sh/uv/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [ty documentation](https://docs.astral.sh/ty/)
- [pytest documentation](https://docs.pytest.org/)
- [PyTorch installation guide](https://pytorch.org/get-started/locally/)

## Next Step

Continue with [Local Training Script](03-local-training-script.md).
