# GPU Training Image

This page adds a GPU-capable training image.

The CPU image from Chapter 3 remains useful. The GPU image exists so the KFP training component can run with CUDA when the cluster schedules it onto a GPU-capable node.

## What You Will Build

You will create:

```text
Dockerfile.gpu
src/kubeflow_by_doing/gpu.py
```

and build:

```text
kubeflow-by-doing/train-gpu:local
```

## Create `Dockerfile.gpu`

Create `Dockerfile.gpu`:

```dockerfile
# syntax=docker/dockerfile:1.7

FROM pytorch/pytorch:2.7.1-cuda12.6-cudnn9-runtime

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --no-install-project

COPY README.md ./
COPY src/ ./src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "kbd"]
```

!!! note

    Keep the PyTorch/CUDA image tag aligned with the local NVIDIA driver and the PyTorch version in `uv.lock`. When upgrading PyTorch, CUDA, or the NVIDIA driver, update this tag intentionally and rerun the Docker and Kubernetes GPU smoke tests before continuing.

`# syntax=docker/dockerfile:1.7` enables the Dockerfile features used below, including the `RUN --mount=type=cache` cache mount.

## Add a CUDA Check Command

Create `src/kubeflow_by_doing/gpu.py`:

```python
"""GPU runtime helpers."""

import torch


def cuda_summary() -> dict[str, str | int | bool]:
    """Return a compact CUDA availability summary."""
    available = torch.cuda.is_available()
    summary: dict[str, str | int | bool] = {
        "cuda_available": available,
        "device_count": torch.cuda.device_count(),
        "torch_version": torch.__version__,
    }

    if available:
        summary["device_name"] = torch.cuda.get_device_name(0)

    return summary
```

Update `src/kubeflow_by_doing/cli.py`:

```python
from kubeflow_by_doing.gpu import cuda_summary


@app.command()
def cuda_check() -> None:
    rprint(cuda_summary())
```

## Build the GPU Image

```bash
docker build -f Dockerfile.gpu -t kubeflow-by-doing/train-gpu:local .
```

## Test with Docker

```bash
docker run --rm --gpus all kubeflow-by-doing/train-gpu:local cuda-check
```

Expected shape:

```text
{
  "cuda_available": true,
  "device_count": 1,
  "device_name": "..."
}
```

Run a tiny training smoke test:

```bash
docker run --rm --gpus all kubeflow-by-doing/train-gpu:local \
  train-model \
  --output-dir /tmp/kbd-gpu-test \
  --epochs 1 \
  --learning-rate 0.001 \
  --seed 42 \
  --device cuda \
  --n-train 32 \
  --n-val 16 \
  --batch-size 8
```

## Make the Image Available to the Cluster

### k3s

Use the repo's chosen k3s image workflow. Because k3s uses Docker as its runtime in this tutorial, the image is available after `docker build`:

```bash
docker images kubeflow-by-doing/train-gpu:local
```

### kind fallback

`kind` remains the CPU fallback cluster in this tutorial. Do not expect the GPU image to validate there unless you have separately set up a GPU-capable `kind` environment outside this tutorial.

Keep using the CPU image path from the earlier chapters on `kind`, and move the GPU image validation to the k3s path.

## Kubernetes GPU Image Smoke Test

Create `infra/gpu/gpu-training-image-smoke.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-training-image-smoke
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  containers:
    - name: cuda-check
      image: kubeflow-by-doing/train-gpu:local
      imagePullPolicy: IfNotPresent
      command: ["uv", "run", "kbd", "cuda-check"]
      resources:
        limits:
          nvidia.com/gpu: 1
```

Apply:

```bash
kubectl apply -f infra/gpu/gpu-training-image-smoke.yaml
kubectl -n kubeflow-by-doing logs pod/gpu-training-image-smoke
kubectl -n kubeflow-by-doing delete pod gpu-training-image-smoke --ignore-not-found
```

## Keep the CPU Image

Do not replace the CPU image.

Keep both:

```text
kubeflow-by-doing/train:local      # CPU/default
kubeflow-by-doing/train-gpu:local  # GPU
```

This lets the CPU and GPU pipelines keep separate runtime contracts:

```text
CPU image: Python base image, device=cpu
GPU image: PyTorch CUDA base image, device=cuda
```

## Acceptance Criteria

You are done when:

- `Dockerfile.gpu` exists
- `kubeflow-by-doing/train-gpu:local` builds
- `docker run --gpus all ... cuda-check` reports CUDA available
- the image is available to k3s
- a Kubernetes pod can run `cuda-check` with `nvidia.com/gpu: 1`
- the CPU image still exists and still works

## References

- [PyTorch Docker images](https://hub.docker.com/r/pytorch/pytorch)
- [NVIDIA CUDA container images](https://hub.docker.com/r/nvidia/cuda)
- [kind loading images](https://kind.sigs.k8s.io/docs/user/quick-start/#loading-an-image-into-your-cluster)

## Next Step

Continue with [GPU-Aware KFP Component](03-gpu-aware-kfp-component.md).
