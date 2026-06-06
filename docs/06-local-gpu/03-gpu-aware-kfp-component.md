# GPU-Aware KFP Component

This page updates the KFP training component so it can request a GPU.

## What You Will Build

You will update:

```text
components/train_model.py
pipelines/image_classification_pipeline.py
```

The training component will support:

```text
accelerator = "cpu"
accelerator = "gpu"
```

CPU mode uses:

```text
kubeflow-by-doing/train:local
```

GPU mode uses:

```text
kubeflow-by-doing/train:gpu-local
```

## Update the Training Component

Update `components/train_model.py` so the component can receive the image and device as parameters.

Target structure:

```python
from __future__ import annotations

from kfp import dsl
from kfp.dsl import Model, Output


@dsl.container_component
def train_model(
    model: Output[Model],
    image: str,
    device: str,
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
    run_id: str = "manual-kfp-001",
    upload_artifacts: bool = False,
    tracking: bool = False,
    image_tag: str = "unknown",
    git_sha: str = "unknown",
) -> dsl.ContainerSpec:
    args = [
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
        device,
        "--n-train",
        n_train,
        "--n-val",
        n_val,
        "--batch-size",
        batch_size,
        "--run-id",
        run_id,
        "--image-tag",
        image_tag,
        "--git-sha",
        git_sha,
    ]

    if upload_artifacts:
        args.append("--upload-artifacts")

    if tracking:
        args.append("--tracking")

    return dsl.ContainerSpec(
        image=image,
        args=args,
    )
```

!!! note

    Do not override `command` here. The training image already defines `ENTRYPOINT ["uv", "run", "kbd"]`, so the component only needs to pass the command arguments.

!!! note

    Codex should verify the installed KFP SDK accepts parameterized container images and non-string arguments in `dsl.ContainerSpec`. If not, adapt to the SDK-supported pattern and keep the same public tutorial behavior.

## Add a Helper for GPU Resources

In `pipelines/image_classification_pipeline.py`, define:

```python
from kfp import dsl


def configure_training_resources(
    task: dsl.PipelineTask,
    accelerator: str,
    gpu_count: int,
) -> dsl.PipelineTask:
    if accelerator == "gpu":
        task.set_accelerator_type("nvidia.com/gpu")
        task.set_accelerator_limit(gpu_count)
        task.set_cpu_request("2")
        task.set_memory_request("4Gi")
        task.set_memory_limit("8Gi")
    else:
        task.set_cpu_request("1")
        task.set_memory_request("2Gi")
        task.set_memory_limit("4Gi")

    return task
```

This is the KFP v2 accelerator API pattern the tutorial expects:

```text
nvidia.com/gpu: 1
```

## Update Pipeline Parameters

Add parameters:

```python
accelerator: str = "cpu"
gpu_count: int = 1
cpu_image: str = "kubeflow-by-doing/train:local"
gpu_image: str = "kubeflow-by-doing/train:gpu-local"
```

Derive image and device:

```python
training_image = gpu_image if accelerator == "gpu" else cpu_image
training_device = "cuda" if accelerator == "gpu" else "cpu"
```

Create and configure the training task:

```python
train_task = train_model(
    image=training_image,
    device=training_device,
    epochs=epochs,
    learning_rate=learning_rate,
    seed=seed,
    n_train=n_train,
    n_val=n_val,
    batch_size=batch_size,
    run_id=run_id,
    upload_artifacts=True,
    tracking=True,
    image_tag=training_image,
    git_sha=git_sha,
)

configure_training_resources(
    task=train_task,
    accelerator=accelerator,
    gpu_count=gpu_count,
)
```

## Keep Evaluation on CPU

Evaluation can stay on CPU for now.

```text
GPU request applies to train_model only
evaluate_model stays CPU
```

## Why Not Always Use `device=auto`?

`device=auto` is convenient locally, but it can hide platform mistakes.

For a GPU KFP run, use:

```text
device=cuda
```

That way the component fails clearly if CUDA is not available.

For CPU fallback, use:

```text
device=cpu
```

## Compile

```bash
uv run python pipelines/image_classification_pipeline.py
```

Inspect the compiled pipeline:

```bash
grep -n "nvidia.com/gpu\\|accelerator\\|gpu" compiled/image_classification_pipeline.yaml || true
```

## Common Problems

### KFP SDK method names differ

GPU resource APIs have changed across KFP versions.

Do not change the tutorial goal. Adapt the helper to the installed SDK.

### Parameterized image does not compile

If the SDK does not support parameterized images cleanly, use two explicit components or an `if` branch in the pipeline.

Keep the behavior:

```text
accelerator=cpu uses CPU image
accelerator=gpu uses GPU image
```

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

## Acceptance Criteria

You are done when:

- the training component accepts image and device parameters
- the pipeline accepts `accelerator`, `gpu_count`, `cpu_image`, and `gpu_image`
- GPU mode configures a GPU resource request
- CPU mode does not request a GPU
- evaluation still works on CPU
- the compiled pipeline is ready for both CPU and GPU runs

## References

- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)
- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [Kubeflow Pipelines concepts](https://www.kubeflow.org/docs/components/pipelines/concepts/pipeline/)

## Next Step

Continue with [Run GPU and CPU Pipelines](04-run-gpu-and-cpu-pipelines.md).
