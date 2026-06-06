# Run a Pipeline from Python

Uploading a pipeline through the UI is useful for learning.

For repeatable workflows, you also want to compile and submit pipelines from code.

## What You Will Build

You will create a small script that submits a pipeline run to the local KFP API.

## Why This Matters

Manual UI runs are not enough for real workflows.

Eventually you want to:

- submit pipeline runs from scripts
- trigger runs from CI
- parameterize runs
- keep pipeline execution reproducible
- avoid click-based workflows

This page introduces that pattern.

## Start Port Forwarding to the KFP API

The UI and API are separate services.

Port-forward the KFP API service:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline 8888:8888
```

Keep this terminal open.

## Create the Submit Script

Create `pipelines/submit_hello_pipeline.py`:

```python
from pathlib import Path

from kfp import Client, compiler
from pipelines.hello_pipeline import hello_pipeline


PIPELINE_PACKAGE = Path("compiled/hello_pipeline.yaml")


def main() -> None:
    PIPELINE_PACKAGE.parent.mkdir(parents=True, exist_ok=True)

    compiler.Compiler().compile(
        pipeline_func=hello_pipeline,
        package_path=str(PIPELINE_PACKAGE),
    )

    client = Client(host="http://localhost:8888")

    run = client.create_run_from_pipeline_package(
        pipeline_file=str(PIPELINE_PACKAGE),
        arguments={"name": "submitted-from-python"},
        run_name="hello-pipeline-from-python",
    )

    print(f"submitted run_id={run.run_id}")


if __name__ == "__main__":
    main()
```

## Make `pipelines` Importable

Create:

```bash
touch pipelines/__init__.py
```

## Submit the Pipeline

In another terminal:

```bash
uv run python -m pipelines.submit_hello_pipeline
```

Run modules under `pipelines/` with `python -m ...` from the repository root. That keeps the repo root on Python's import path, so imports like `from pipelines...` and `from components...` resolve consistently.

Expected output:

```text
submitted run_id=...
```

Open the KFP UI and inspect the run.

## Common Problems

### `ConnectionRefusedError`

The KFP API port-forward is not running.

Start it:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline 8888:8888
```

### Import error for `pipelines.hello_pipeline`

Make sure `pipelines/__init__.py` exists and run the script as a module from the repository root.

```bash
touch pipelines/__init__.py
uv run python -m pipelines.submit_hello_pipeline
```

### The run is submitted but fails

Inspect the KFP UI first.

Then inspect Kubernetes pods and events:

```bash
kubectl get pods -A
kubectl get events -A --sort-by=.lastTimestamp
```

## UI vs Python Submission

Use the UI when:

- learning
- manually inspecting a pipeline
- debugging interactively

Use Python submission when:

- automating runs
- integrating with CI
- running experiments repeatedly
- enforcing a reproducible run configuration

## Cleanup

No cleanup is required.

Stop port forwarding with `Ctrl+C` when done.

## What You Learned

You submitted a KFP run from Python.

This is the basis for later CI/CD and scheduled execution chapters.

## References

- [Run a pipeline](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/run-a-pipeline/)
- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)

## Acceptance Criteria

You are done when:

- the KFP API port-forward is running
- `uv run python -m pipelines.submit_hello_pipeline` submits a run
- the submitted run appears in the KFP UI
- the run completes successfully

## Next Step

Continue with [Components, Parameters, and Artifacts](04-components-parameters-artifacts.md).
