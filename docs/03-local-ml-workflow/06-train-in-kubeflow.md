# Train in Kubeflow

This page wraps the containerized training workflow as Kubeflow components.

## What You Will Build

Create:

```text
components/train_model.py
components/evaluate_model.py
pipelines/image_classification_pipeline.py
```

The pipeline will run:

```text
train_model → evaluate_model
```

inside Kubeflow.

## Why This Matters

By this point, the code already works:

```text
locally
in tests
inside a container
inside Kubernetes
```

Now Kubeflow adds orchestration:

- parameterized runs
- step graph
- run history
- logs
- artifacts
- metrics

The component wrapper should be thin because the package and image already do the real work.

## Create the Training Component

Create `components/train_model.py`:

```python
from __future__ import annotations

from kfp import dsl
from kfp.dsl import Model, Output


@dsl.container_component
def train_model(
    model: Output[Model],
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image="kubeflow-by-doing/train:local",
        args=[
            "train-model",
            "--output-dir",
            model.path,
            "--epochs",
            epochs,
            "--learning-rate",
            learning_rate,
            "--seed",
            seed,
            "--device",
            "cuda",
            "--n-train",
            n_train,
            "--n-val",
            n_val,
            "--batch-size",
            batch_size,
        ],
    )
```

The component does not set `command=["kbd"]` because the image already defines `ENTRYPOINT ["uv", "run", "kbd"]`.

## Create the Evaluation Component

Create `components/evaluate_model.py`:

```python
from __future__ import annotations

from kfp import dsl
from kfp.dsl import Input, Model, OutputPath


@dsl.container_component
def evaluate_model(
    model: Input[Model],
    metrics_artifact: OutputPath("Dataset"),
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> dsl.ContainerSpec:
    return dsl.ContainerSpec(
        image="kubeflow-by-doing/train:local",
        args=[
            "evaluate-model",
            "--model-dir",
            model.path,
            "--metrics-path",
            metrics_artifact,
            "--seed",
            seed,
            "--device",
            "cuda",
            "--n-train",
            n_train,
            "--n-val",
            n_val,
            "--batch-size",
            batch_size,
        ],
    )
```

## Create the Pipeline

Create `pipelines/image_classification_pipeline.py`:

```python
from __future__ import annotations

from kfp import compiler, dsl

from components.evaluate_model import evaluate_model
from components.train_model import train_model


@dsl.pipeline(name="image-classification-local")
def image_classification_pipeline(
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> None:
    train_task = train_model(
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )

    evaluate_model(
        model=train_task.outputs["model"],
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=image_classification_pipeline,
        package_path="compiled/image_classification_pipeline.yaml",
    )
```

## Compile the Pipeline

```bash
uv run python -m pipelines.image_classification_pipeline
```

Verify:

```bash
ls -lh compiled/image_classification_pipeline.yaml
```

## Import the Image into the GPU-Capable Local Cluster

If you rebuilt the image, reload it:

```bash
mkdir -p build
docker save kubeflow-by-doing/train:local > build/train-image.tar
sudo microk8s ctr image import build/train-image.tar
```

## Run in KFP

Port-forward the KFP UI:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

Open:

```text
http://localhost:8080
```

Upload:

```text
compiled/image_classification_pipeline.yaml
```

Run with:

```text
epochs: 2
learning_rate: 0.001
seed: 42
```

## Inspect the Run

In the KFP UI:

- verify the graph has training and evaluation steps
- inspect logs
- inspect model artifact
- inspect metrics if available

## Common Problems

### `ImagePullBackOff`

The image exists locally in Docker but not inside the active cluster.

```bash
docker save kubeflow-by-doing/train:local > build/train-image.tar
sudo microk8s ctr image import build/train-image.tar
```

### Component cannot find `kbd`

Check the image locally:

```bash
docker run --rm kubeflow-by-doing/train:local --help
```

If it fails locally, fix the Dockerfile before debugging KFP.

### Metrics do not show in the UI

First verify that evaluation writes a valid metrics file.

Then refine the component wrapper according to KFP's metrics artifact expectations.

## Acceptance Criteria

You are done when:

- training and evaluation component files exist
- the pipeline file exists
- `compiled/image_classification_pipeline.yaml` is generated
- the image is imported into the GPU-capable local cluster
- the pipeline runs in KFP
- the training step produces a model artifact
- the evaluation step produces metrics or a metrics artifact
- you can debug the step pods with `kubectl`

## References

- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)
- [KFP container components](https://www.kubeflow.org/docs/components/pipelines/user-guides/components/container-components/)
- [Compile a pipeline](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/compile-a-pipeline/)
- [MicroK8s local image import](https://microk8s.io/docs/registry-images)

## Next Step

Continue with [Evaluation Gates](07-evaluation-gates.md).
