# Components, Parameters, and Artifacts

The first pipeline passed a string between two steps.

Real ML workflows need more structure:

- parameters configure behavior
- artifacts represent files and directories
- metrics summarize results
- components separate workflow steps

This page introduces those concepts with a tiny ML-shaped pipeline.

If you are following along in the repository, this page is the target implementation for `pipelines/tiny_ml_pipeline.py`.

## What You Will Build

You will build a three-step pipeline:

```text
generate_dataset → train_model → evaluate_model
```

The model is fake for now. The workflow shape is real.

## Why This Matters

In a local Python script, it is tempting to rely on implicit state:

- local files
- global variables
- hardcoded paths
- current working directory
- hidden environment variables

In Kubeflow, each component should make its inputs and outputs explicit.

That explicit boundary is one of the main benefits of pipelines.

## Create the Pipeline

Create `pipelines/tiny_ml_pipeline.py`:

```python
from kfp import compiler, dsl
from kfp.dsl import Dataset, Input, Metrics, Model, Output


@dsl.component(base_image="python:3.12-slim")
def generate_dataset(dataset: Output[Dataset], n_samples: int = 100) -> None:
    from pathlib import Path
    import json
    import random

    path = Path(dataset.path)
    path.mkdir(parents=True, exist_ok=True)

    samples = [
        {"x": random.random(), "y": random.randint(0, 1)}
        for _ in range(n_samples)
    ]

    (path / "data.json").write_text(json.dumps(samples), encoding="utf-8")


@dsl.component(base_image="python:3.12-slim")
def train_model(
    dataset: Input[Dataset],
    model: Output[Model],
    learning_rate: float = 0.01,
) -> None:
    from pathlib import Path
    import json

    data_path = Path(dataset.path) / "data.json"
    samples = json.loads(data_path.read_text(encoding="utf-8"))

    model_path = Path(model.path)
    model_path.mkdir(parents=True, exist_ok=True)

    # This is intentionally not real ML yet.
    # The point is to create a model artifact.
    artifact = {
        "kind": "tiny-threshold-model",
        "learning_rate": learning_rate,
        "n_samples": len(samples),
        "threshold": 0.5,
    }

    (model_path / "model.json").write_text(json.dumps(artifact), encoding="utf-8")


@dsl.component(base_image="python:3.12-slim")
def evaluate_model(
    model: Input[Model],
    metrics: Output[Metrics],
) -> None:
    from pathlib import Path
    import json

    model_path = Path(model.path) / "model.json"
    model_data = json.loads(model_path.read_text(encoding="utf-8"))

    # Fake metric for now.
    accuracy = 0.90 if model_data["n_samples"] >= 50 else 0.70

    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("n_samples", model_data["n_samples"])


@dsl.pipeline(name="tiny-ml-pipeline")
def tiny_ml_pipeline(
    n_samples: int = 100,
    learning_rate: float = 0.01,
) -> None:
    dataset_task = generate_dataset(n_samples=n_samples)
    model_task = train_model(
        dataset=dataset_task.outputs["dataset"],
        learning_rate=learning_rate,
    )
    evaluate_model(model=model_task.outputs["model"])


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=tiny_ml_pipeline,
        package_path="compiled/tiny_ml_pipeline.yaml",
    )
```

## Compile the Pipeline

```bash
uv run python -m pipelines.tiny_ml_pipeline
```

Verify:

```bash
ls -lh compiled/tiny_ml_pipeline.yaml
```

## Run the Pipeline

You can upload `compiled/tiny_ml_pipeline.yaml` through the KFP UI.

Use parameters:

```text
n_samples: 100
learning_rate: 0.01
```

After the run completes, inspect:

- graph
- step logs
- artifacts
- metrics

## Run a Low-Sample Variant

Create a second run with:

```text
n_samples: 10
learning_rate: 0.01
```

The fake metric should be lower.

This simulates why parameters matter.

## What Are Artifacts?

Artifacts represent files or directories produced by a step and consumed by another step.

In this pipeline:

```text
generate_dataset produces Dataset
train_model consumes Dataset and produces Model
evaluate_model consumes Model and produces Metrics
```

The actual paths are managed by KFP.

The important habit is to pass data explicitly rather than assuming shared local files.

## What Are Metrics?

Metrics are scalar values associated with a run or step.

Examples:

- accuracy
- loss
- F1 score
- IoU
- latency
- number of samples

In later chapters, metrics will control promotion decisions.

## Common Problems

### `ImportError` for `Dataset`, `Model`, or `Metrics`

Check your KFP SDK version:

```bash
uv run python - <<'PY'
import kfp
print(kfp.__version__)
PY
```

Use a recent KFP v2 SDK.

### Component fails with file not found

Inspect the failed step logs.

Common causes:

- reading from the wrong artifact path
- assuming a file exists directly at `artifact.path`
- forgetting to create a directory before writing

### Metrics do not show up

Check that the component uses:

```python
metrics.log_metric("accuracy", accuracy)
```

and that `metrics` is typed as:

```python
metrics: Output[Metrics]
```

## Cleanup

No cleanup is required.

The compiled pipeline YAML can stay in `compiled/` for later chapters.

## What You Learned

You passed parameters explicitly, used typed artifacts to move data between steps, and recorded scalar metrics from a Kubeflow component.

That workflow shape is the basis for the rest of the tutorial.

## References

- [Kubeflow Pipelines components](https://www.kubeflow.org/docs/components/pipelines/user-guides/components/)
- [Kubeflow Pipelines parameters, artifacts, and metrics](https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/parameters-artifacts/)
- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)

## Acceptance Criteria

You are done when:

- `pipelines/tiny_ml_pipeline.py` compiles successfully
- the pipeline accepts `n_samples` and `learning_rate` parameters
- the run produces a `Dataset`, a `Model`, and `Metrics`
- the metrics view shows the recorded values

## Next Step

Continue with [Reusable Components](05-reusable-components.md).
