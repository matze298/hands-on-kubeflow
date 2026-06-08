# Reusable Components

The previous page defined all components in one file.

That is fine for learning, but real projects need components that can be tested, reused, and eventually containerized with project code.

If you are following along in the repository, this page is the target implementation for the `components/` package plus `pipelines/tiny_ml_pipeline_refactored.py`.

## What You Will Build

You will refactor the tiny ML pipeline into:

```text
components/
├── generate_dataset.py
├── train_model.py
└── evaluate_model.py

pipelines/
└── tiny_ml_pipeline_refactored.py
```

## Why This Matters

A pipeline file should compose workflow steps.

It should not become the only place where all project logic lives.

Good component boundaries make it easier to:

- test logic locally
- reuse steps across pipelines
- containerize components later
- review changes
- debug failures
- replace toy logic with real PyTorch code

## Create Component Modules

Create the folder:

```bash
mkdir -p components
touch components/__init__.py
```

Create `components/generate_dataset.py`:

```python
from kfp import dsl
from kfp.dsl import Dataset, Output


@dsl.component(base_image="python:3.12-slim")
def generate_dataset(dataset: Output[Dataset], n_samples: int = 100) -> None:
    from pathlib import Path
    import json
    import random

    path = Path(dataset.path)
    path.mkdir(parents=True, exist_ok=True)

    samples = [{"x": random.random(), "y": random.randint(0, 1)} for _ in range(n_samples)]

    (path / "data.json").write_text(json.dumps(samples), encoding="utf-8")
```

Create `components/train_model.py`:

```python
from kfp import dsl
from kfp.dsl import Dataset, Input, Model, Output


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

    artifact = {
        "kind": "tiny-threshold-model",
        "learning_rate": learning_rate,
        "n_samples": len(samples),
        "threshold": 0.5,
    }

    (model_path / "model.json").write_text(json.dumps(artifact), encoding="utf-8")
```

Create `components/evaluate_model.py`:

```python
from kfp import dsl
from kfp.dsl import Input, Metrics, Model, Output


@dsl.component(base_image="python:3.12-slim")
def evaluate_model(
    model: Input[Model],
    metrics: Output[Metrics],
) -> None:
    from pathlib import Path
    import json

    model_path = Path(model.path) / "model.json"
    model_data = json.loads(model_path.read_text(encoding="utf-8"))

    accuracy = 0.90 if model_data["n_samples"] >= 50 else 0.70

    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("n_samples", model_data["n_samples"])
```

## Create the Refactored Pipeline

Create `pipelines/tiny_ml_pipeline_refactored.py`:

```python
from kfp import compiler, dsl

from components.evaluate_model import evaluate_model
from components.generate_dataset import generate_dataset
from components.train_model import train_model


@dsl.pipeline(name="tiny-ml-pipeline-refactored")
def tiny_ml_pipeline_refactored(
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
        pipeline_func=tiny_ml_pipeline_refactored,
        package_path="compiled/tiny_ml_pipeline_refactored.yaml",
    )
```

## Compile

```bash
uv run python -m pipelines.tiny_ml_pipeline_refactored
```

Verify:

```bash
ls -lh compiled/tiny_ml_pipeline_refactored.yaml
```

## Run

Upload the compiled YAML in the KFP UI or submit it with a Python script.

Use:

```text
n_samples: 100
learning_rate: 0.01
```

## What About Unit Tests?

The components above are still KFP-decorated functions, so they are not ideal for pure unit testing.

In Chapter 3, we will separate core Python logic from KFP wrappers:

```text
src/kubeflow_by_doing/
  data.py
  train.py
  evaluate.py

components/
  generate_dataset.py
  train_model.py
  evaluate_model.py
```

That gives us:

```text
testable Python functions
  ↓
thin KFP component wrappers
  ↓
pipeline composition
```

For now, the goal is simply to stop putting all component definitions in one pipeline file.

## Common Problems

### `ModuleNotFoundError: No module named 'components'`

Make sure you run commands from the repository root and that this file exists:

```bash
touch components/__init__.py
```

### Refactored pipeline compiles but run fails

Inspect the failed step logs.

The most common issue is an import inside the component body. Remember that code inside the component runs in the component container, not in your local Python process.

Because these components use only the Python standard library inside the component body, they should work with `python:3.12-slim`.

### Why are imports inside the function?

For lightweight Python components, imports inside the component function make dependencies explicit inside the generated component.

Later, when we use project containers, we can move more logic into package modules and use custom images.

## Cleanup

No cleanup is required.

## What You Learned

You refactored a pipeline into reusable component modules.

You also saw the next design step:

```text
core logic in src/
thin wrappers in components/
composition in pipelines/
```

## References

- [Kubeflow Pipelines components](https://www.kubeflow.org/docs/components/pipelines/user-guides/components/)
- [Kubeflow Pipelines Python component guide](https://www.kubeflow.org/docs/components/pipelines/user-guides/components/python-components/)
- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)

## Acceptance Criteria

You are done when:

- component files exist under `components/`
- the refactored pipeline compiles
- the refactored pipeline runs successfully
- the run produces metrics
- you can explain the difference between component logic and pipeline composition

## Next Step

Continue with [Debugging KFP Runs](06-debugging-kfp-runs.md).
