# Compile Pipelines

This page adds CI pipeline compilation.

## What You Will Build

You will create:

```text
ci/compile_pipeline.py
.github/workflows/compile-pipelines.yaml
```

The workflow compiles:

```text
pipelines/image_classification_pipeline.py
```

into:

```text
compiled/image_classification_pipeline.yaml
```

and uploads the compiled YAML as a CI artifact.

## Why This Matters

Pipeline compilation should be reproducible.

If a pipeline only compiles on one laptop, it is not yet production-shaped.

CI should answer:

```text
Does the pipeline compile from a clean checkout?
```

## Create `ci/compile_pipeline.py`

```python
from __future__ import annotations

from pathlib import Path

from kfp import compiler

from pipelines.image_classification_pipeline import image_classification_pipeline


def main() -> None:
    output_path = Path("compiled/image_classification_pipeline.yaml")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    compiler.Compiler().compile(
        pipeline_func=image_classification_pipeline,
        package_path=str(output_path),
    )

    print(f"compiled pipeline: {output_path}")


if __name__ == "__main__":
    main()
```

## Create `.github/workflows/compile-pipelines.yaml`

```yaml
name: Compile Pipelines

on:
  pull_request:
  push:
    branches:
      - main
  workflow_dispatch:

permissions:
  contents: read

jobs:
  compile:
    name: Compile KFP pipelines
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.14

      - name: Sync dependencies
        run: uv sync --all-groups --frozen

      - name: Compile pipeline
        run: uv run python ci/compile_pipeline.py

      - name: Show compiled pipeline
        run: |
          ls -lh compiled/
          grep -n "image-classification" compiled/image_classification_pipeline.yaml || true

      - name: Upload compiled pipeline
        uses: actions/upload-artifact@v4
        with:
          name: compiled-pipelines
          path: compiled/*.yaml
          if-no-files-found: error
```

## Optional: Check for Uncommitted Compiled Changes

If compiled pipelines are committed, add:

```yaml
      - name: Check compiled pipeline is committed
        run: |
          git diff -- compiled/
          git diff --exit-code -- compiled/
```

If compiled pipelines are CI artifacts only, do not add this.

## Compile Locally

```bash
uv run python ci/compile_pipeline.py
```

Verify:

```bash
ls -lh compiled/image_classification_pipeline.yaml
```

## Common Problems

### Import error for `pipelines`

Run from repository root and make sure `pipelines/__init__.py` exists.

### KFP SDK differs between local and CI

Pin dependencies in `uv.lock` and commit the lockfile.

### Compiled pipeline changes on every run

Check for timestamps, random IDs, or non-deterministic default values.

## Acceptance Criteria

You are done when:

- `ci/compile_pipeline.py` exists
- compile workflow exists
- pipeline compiles in CI
- compiled YAML is uploaded as an artifact
- the repository has a clear policy for committing or not committing compiled YAML

## References

- [Kubeflow Pipelines compile a pipeline](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/compile-a-pipeline/)
- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)
- [GitHub Actions artifacts](https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts)

## Next Step

Continue with [Submit Pipelines](04-submit-pipelines.md).
