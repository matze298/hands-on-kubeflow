# Evaluation Gates

This page adds a simple quality gate to the local ML pipeline.

The pipeline should not blindly promote every trained model.

## What You Will Build

Extend the pipeline from:

```text
train_model → evaluate_model
```

to:

```text
train_model → evaluate_model → conditionally_promote
```

The first promotion step can be simple:

```text
if accuracy >= threshold:
    write promotion marker
else:
    skip promotion
```

## Why This Matters

A useful ML pipeline encodes decisions:

- did the run complete?
- are the metrics good enough?
- should the model be promoted?
- should deployment happen?
- should the run stop?

This page introduces that idea with a small metric threshold.

## Add a Promotion Component

Create `components/promote_model.py`:

```python
from __future__ import annotations

from kfp import dsl
from kfp.dsl import Artifact, Input, Model, Output


@dsl.component(base_image="python:3.12-slim")
def read_accuracy(metrics_path: str) -> float:
    from pathlib import Path
    import json

    metrics = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
    return float(metrics["accuracy"])


@dsl.component(base_image="python:3.12-slim")
def promote_model(
    model: Input[Model],
    promotion: Output[Artifact],
    accuracy: float,
    min_accuracy: float = 0.8,
) -> None:
    from pathlib import Path
    import json

    promotion_path = Path(promotion.path)
    promotion_path.parent.mkdir(parents=True, exist_ok=True)
    promotion_path.write_text(
        json.dumps(
            {
                "status": "promoted",
                "accuracy": accuracy,
                "min_accuracy": min_accuracy,
                "model_uri": model.uri,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
```

## Add Conditional Execution

Update `pipelines/image_classification_pipeline.py`:

```python
from __future__ import annotations

from kfp import compiler, dsl

from components.evaluate_model import evaluate_model
from components.promote_model import promote_model, read_accuracy
from components.train_model import train_model


@dsl.pipeline(name="image-classification-local")
def image_classification_pipeline(
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
    min_accuracy: float = 0.8,
) -> None:
    train_task = train_model(
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )

    evaluate_task = evaluate_model(
        model=train_task.outputs["model"],
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )

    accuracy_task = read_accuracy(metrics_path=evaluate_task.outputs["metrics_artifact"])

    with dsl.If(accuracy_task.output >= min_accuracy):
        promote_model(
            model=train_task.outputs["model"],
            accuracy=accuracy_task.output,
            min_accuracy=min_accuracy,
        )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=image_classification_pipeline,
        package_path="compiled/image_classification_pipeline.yaml",
    )
```

This keeps the default tutorial behavior simple: if the threshold is not met, the promotion step is skipped instead of failing the whole run.

## Run a Passing Case

Use a low threshold:

```text
min_accuracy: 0.5
```

Expected:

```text
train_model → evaluate_model → promote_model
```

## Run a Failing Case

Use a high threshold:

```text
min_accuracy: 0.99
```

Expected:

```text
train_model → evaluate_model → no promotion
```

## Why Skip Instead of Fail

For this tutorial, skipping promotion is cleaner than failing the whole pipeline.

That models a common experimentation workflow:

```text
the run itself was valid
  ↓
the metric threshold was not met
  ↓
promotion does not happen
```

## Common Problems

### Accuracy is not available as a pipeline value

KFP metrics shown in the UI are not always the same thing as values usable for control flow.

That is why this chapter uses a small `read_accuracy` helper component instead of relying only on UI metrics.

### Promotion step runs even when accuracy is low

Check the `dsl.If(...)` condition wiring and inspect the compiled YAML if needed.

### Promotion step fails because model URI is missing

Artifact metadata and paths can differ by KFP version and local setup.

Use a promotion record that includes whatever model path or artifact URI is reliably available.

## Acceptance Criteria

You are done when:

- `components/promote_model.py` exists
- the pipeline accepts `min_accuracy`
- the evaluation step exposes an accuracy value usable by the pipeline
- a passing run promotes the model
- a failing run does not promote the model
- the KFP UI makes the decision visible
- you can explain why this tutorial uses skipping promotion by default

## References

- [KFP control flow](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/control-flow/)
- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)
- [Kubeflow Pipelines documentation](https://www.kubeflow.org/docs/components/pipelines/)

## Next Step

Continue with Chapter 4: Artifacts and Tracking.
