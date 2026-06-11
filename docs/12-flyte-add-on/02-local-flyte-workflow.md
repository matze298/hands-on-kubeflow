# Local Flyte Workflow

This page builds a local Flyte version of the tutorial's image classification workflow.

You will create:

```text
flyte/
`-- kbd_flyte_workflow.py
```

The file reuses:

```text
src/kubeflow_by_doing/train.py
src/kubeflow_by_doing/evaluate.py
```

That reuse is important. The goal is to compare orchestrators, not to create a second ML implementation.

## Verify Flyte

From the repository root:

```bash
uv run flyte --version
```

Expected shape:

```text
Flyte SDK version: 2.x.x
```

Create local Flyte runtime configuration:

```bash
uv run flyte create config --local-persistence
uv run flyte get config
```

The config command creates:

```text
.flyte/config.yaml
```

This is local runtime configuration. It is not part of the Kubeflow core tutorial state.

The repository ignores `.flyte/` because it is machine-local runtime state.

!!! note

    The official Flyte quickstart installs `flyte[tui]` with `pip`. This repository already includes `flyte[tui]` in `pyproject.toml`, so use `uv run flyte ...` from the repository root.

## Create the Flyte Directory

Create:

```bash
mkdir -p flyte
```

This keeps the optional Flyte code separate from the KFP pipeline code:

```text
pipelines/ -> Kubeflow Pipelines definitions
flyte/     -> optional Flyte workflow definitions
```

Do not put Flyte examples into `pipelines/`. That directory is already established as the KFP area.

## Create `flyte/kbd_flyte_workflow.py`

Create `flyte/kbd_flyte_workflow.py`:

```python
import base64
from pathlib import Path
from tempfile import TemporaryDirectory

import flyte

from kubeflow_by_doing.evaluate import evaluate
from kubeflow_by_doing.train import train


env = flyte.TaskEnvironment(name="kubeflow-by-doing-flyte")


@env.task
def train_model_task(
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> str:
    with TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "model"
        train(
            output_dir=output_dir,
            epochs=epochs,
            learning_rate=learning_rate,
            seed=seed,
            device="cpu",
            n_train=n_train,
            n_val=n_val,
            batch_size=batch_size,
        )
        model_bytes = (output_dir / "model.pt").read_bytes()
        return base64.b64encode(model_bytes).decode("ascii")


@env.task
def evaluate_model_task(
    encoded_model: str,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> float:
    with TemporaryDirectory() as tmp_dir:
        model_dir = Path(tmp_dir) / "model"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "model.pt").write_bytes(base64.b64decode(encoded_model))
        metrics_path = Path(tmp_dir) / "metrics.json"
        metrics = evaluate(
            model_dir=model_dir,
            metrics_path=metrics_path,
            seed=seed,
            device="cpu",
            n_train=n_train,
            n_val=n_val,
            batch_size=batch_size,
        )
        return float(metrics["accuracy"])


@env.task
def flyte_image_classification_pipeline(
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
    min_accuracy: float = 0.5,
) -> dict[str, float]:
    encoded_model = train_model_task(
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )
    accuracy = evaluate_model_task(
        encoded_model=encoded_model,
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )
    return {
        "accuracy": accuracy,
        "promoted": 1.0 if accuracy >= min_accuracy else 0.0,
    }
```

This is intentionally a CPU example. GPU execution belongs in the resources page, after the local shape works.

## Understand the Teaching Shortcut

The example encodes `model.pt` as a base64 string:

```python
model_bytes = (output_dir / "model.pt").read_bytes()
return base64.b64encode(model_bytes).decode("ascii")
```

That is acceptable only because the tutorial model is tiny and this page is teaching task shape.

Do not use this pattern for real model artifacts. Real artifacts should move as durable files, directories, or object storage paths. The next page expands that point.

The shortcut is useful here because it keeps the first Flyte example focused on:

- task declaration
- task calls
- parameter passing
- local execution
- promotion decision output

## Run the Workflow Locally

Run:

```bash
export PYTHONPATH="$PWD/src"
uv run flyte run --local flyte/kbd_flyte_workflow.py flyte_image_classification_pipeline
```

The `PYTHONPATH` export makes the `src/` package importable without requiring an editable package install.

Expected behavior:

- Flyte loads `flyte/kbd_flyte_workflow.py`
- `train_model_task` trains the tiny model
- `evaluate_model_task` evaluates it
- the top-level task returns an accuracy and promotion flag

## Pass Parameters

Change the training inputs from the command line:

```bash
export PYTHONPATH="$PWD/src"
uv run flyte run --local flyte/kbd_flyte_workflow.py flyte_image_classification_pipeline \
  --epochs 3 \
  --learning-rate 0.001 \
  --seed 42 \
  --n-train 256 \
  --n-val 64 \
  --batch-size 32 \
  --min-accuracy 0.5
```

Use small values. This add-on is about orchestration, not model quality.

## Inspect Local Runs

Start the local terminal UI:

```bash
uv run flyte start tui
```

Use this to inspect local run records.

Compare that with the KFP path:

```bash
uv run python pipelines/image_classification_pipeline.py
```

The KFP command compiles pipeline YAML. The Flyte command executes the top-level task locally.

## Debug Common Failures

### `ModuleNotFoundError: kubeflow_by_doing`

Check:

```bash
echo "$PYTHONPATH"
```

Set:

```bash
export PYTHONPATH="$PWD/src"
```

Then rerun the Flyte command from the repository root.

### `.flyte/config.yaml` is missing

Run:

```bash
uv run flyte create config --local-persistence
uv run flyte get config
```

Do not run Flyte commands from your home directory. The Flyte quickstart warns against running from `$HOME` because remote packaging can accidentally bundle too much local state. Use the repository root.

### The model payload feels wrong

It is a teaching shortcut. Keep going, then read the next page. The next page explains the remote-ready artifact model.

### The output accuracy changes

The tutorial uses a small synthetic dataset and a small model. Minor changes in parameters can change metrics. Keep the seed fixed when comparing orchestrator behavior.

## Compare Against KFP

The local Flyte workflow has less setup for a first local run:

```text
write task file
run top-level task
inspect TUI
```

The KFP workflow has a stronger connection to the Kubeflow platform:

```text
write pipeline/component code
compile YAML
submit to KFP backend
inspect KFP UI and Kubernetes pods
```

This is the core tradeoff. Flyte can be smoother locally; KFP is the course's native platform.

## Acceptance Criteria

You are done when:

- `flyte/kbd_flyte_workflow.py` exists
- `uv run flyte --version` works
- `.flyte/config.yaml` exists after local config creation
- the local Flyte workflow runs from the repository root
- you can explain why `PYTHONPATH="$PWD/src"` is used
- you can explain why the base64 model handoff is not production-ready

## References

- [Flyte quickstart](https://www.union.ai/docs/v2/flyte/user-guide/quickstart/)
- [Flyte tasks](https://www.union.ai/docs/v2/flyte/user-guide/core-concepts/tasks/)

## Next Step

Continue with [Artifacts, Resources, and Secrets](03-artifacts-resources-and-secrets.md).
