# GPU-Aware KFP Component

This page adds a separate GPU KFP pipeline instead of overwriting the Chapter 3 CPU pipeline.

## What You Will Build

You will create:

```text
components/train_model_gpu.py
pipelines/image_classification_gpu_pipeline.py
compiled/image_classification_gpu_pipeline.yaml
```

The Chapter 3 CPU artifacts stay available:

```text
Dockerfile
kubeflow-by-doing/train:local
compiled/image_classification_pipeline.yaml
```

The Chapter 6 GPU artifacts are separate:

```text
Dockerfile.gpu
kubeflow-by-doing/train-gpu:local
compiled/image_classification_gpu_pipeline.yaml
```

## Create the GPU Training Component

Create `components/train_model_gpu.py`:

```python
from kfp.dsl import Model, Output
from kfp.dsl.container_component_decorator import container_component
from kfp.dsl.structures import ContainerSpec


@container_component
def train_model_gpu(  # noqa: PLR0913, PLR0917
    model: Output[Model],
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> ContainerSpec:
    return ContainerSpec(
        image="kubeflow-by-doing/train-gpu:local",
        command=["uv", "run", "kbd"],
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

## Reuse CPU Evaluation

Keep using `components/evaluate_model.py` from Chapter 3:

```python
from kfp.dsl import Input, Model, OutputPath
from kfp.dsl.container_component_decorator import container_component
from kfp.dsl.structures import ContainerSpec


@container_component
def evaluate_model(  # noqa: PLR0913, PLR0917
    model: Input[Model],
    metrics_artifact: OutputPath("Dataset"),
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> ContainerSpec:
    return ContainerSpec(
        image="kubeflow-by-doing/train:local",
        command=["uv", "run", "kbd"],
        args=[
            "evaluate-model",
            "--model-dir",
            model.path,
            "--metrics-path",
            metrics_artifact,
            "--seed",
            seed,
            "--device",
            "cpu",
            "--n-train",
            n_train,
            "--n-val",
            n_val,
            "--batch-size",
            batch_size,
        ],
    )
```

The GPU request applies only to training. Evaluation uses the Chapter 3 CPU image.

## Create the GPU Pipeline

Create `pipelines/image_classification_gpu_pipeline.py`:

```python
import sys
from pathlib import Path

from kfp.compiler.compiler import Compiler
from kfp.dsl.pipeline_context import pipeline

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.evaluate_model import evaluate_model  # noqa: E402
from components.train_model_gpu import train_model_gpu  # noqa: E402


@pipeline(name="image-classification-gpu")
def image_classification_gpu_pipeline(  # noqa: PLR0913, PLR0917
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> None:
    train_task = train_model_gpu(
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )
    train_task.set_accelerator_type("nvidia.com/gpu")
    train_task.set_accelerator_limit(1)
    train_task.set_cpu_request("2")
    train_task.set_memory_request("4Gi")
    train_task.set_memory_limit("8Gi")

    evaluate_model(
        model=train_task.outputs["model"],
        seed=seed,
        n_train=n_train,
        n_val=n_val,
        batch_size=batch_size,
    )


if __name__ == "__main__":
    Compiler().compile(
        pipeline_func=image_classification_gpu_pipeline,
        package_path="compiled/image_classification_gpu_pipeline.yaml",
    )
```

## Compile

```bash
uv run python pipelines/image_classification_gpu_pipeline.py
```

Inspect the compiled pipeline:

```bash
grep -n "nvidia.com/gpu\\|train-gpu:local\\|train:local" compiled/image_classification_gpu_pipeline.yaml
```

Expected:

```text
image: kubeflow-by-doing/train-gpu:local
resourceType: nvidia.com/gpu
image: kubeflow-by-doing/train:local
```

## Why Not Use `device=auto`?

`device=auto` is convenient locally, but it can hide platform mistakes.

For the GPU KFP run, use:

```text
device=cuda
```

That way the component fails clearly if CUDA is not available.

## Common Problems

### GPU request is missing from pod

Run the GPU pipeline, then inspect the training pod:

```bash
kubectl describe pod -n <namespace> <training-pod>
```

Look for:

```text
Limits:
  nvidia.com/gpu: 1
```

### The pod requests a GPU but PyTorch says CUDA is unavailable

Check that the task uses the GPU image and that the node advertises GPU capacity:

```bash
grep -n "train-gpu:local\\|nvidia.com/gpu" compiled/image_classification_gpu_pipeline.yaml
kubectl describe nodes | grep -A5 -B5 "nvidia.com/gpu"
```

## Acceptance Criteria

You are done when:

- `components/train_model_gpu.py` exists
- `components/evaluate_model.py` still runs evaluation on CPU
- `pipelines/image_classification_gpu_pipeline.py` exists
- `compiled/image_classification_gpu_pipeline.yaml` contains `nvidia.com/gpu`
- the Chapter 3 CPU pipeline still exists separately
- evaluation still works on CPU

## References

- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)
- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [Kubeflow Pipelines concepts](https://www.kubeflow.org/docs/components/pipelines/concepts/pipeline/)

## Next Step

Continue with [Run GPU and CPU Pipelines](04-run-gpu-and-cpu-pipelines.md).
