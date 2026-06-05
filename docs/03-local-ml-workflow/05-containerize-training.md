# Containerize Training

This page turns the local training code into a container image.

The image will later be used by Kubeflow components.

## What You Will Build

Create a `Dockerfile` that can run:

```bash
kbd train-model ...
kbd evaluate-model ...
```

inside a container.

Then import the image into the GPU-capable `MicroK8s` cluster from Chapter 1.

## Why This Matters

Kubeflow does not run your local virtual environment.

Kubeflow runs containers.

```text
Python package
  ↓
dependencies
  ↓
entrypoint
  ↓
container image
  ↓
Kubernetes pod
  ↓
Kubeflow component
```

If the image is wrong, the pipeline step is wrong.

## Create the Dockerfile

Create `Dockerfile` in the repository root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY src/ ./src/

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "kbd"]
```

This keeps the image invocation model simple:

- `docker run ... train-model ...` expands to `uv run kbd train-model ...`
- KFP container components can reuse the image entrypoint and pass only CLI arguments

## Build the Image

```bash
docker build -t kubeflow-by-doing/train:local .
```

Verify:

```bash
docker images | grep kubeflow-by-doing
```

## Run Training in the Container

```bash
mkdir -p outputs/container-train

docker run --rm \
  -v "$PWD/outputs/container-train:/outputs" \
  kubeflow-by-doing/train:local \
  train-model \
  --output-dir /outputs \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --device auto
```

Verify:

```bash
ls -lh outputs/container-train
```

## Run Evaluation in the Container

```bash
docker run --rm \
  -v "$PWD/outputs/container-train:/outputs" \
  kubeflow-by-doing/train:local \
  evaluate-model \
  --model-dir /outputs \
  --metrics-path /outputs/metrics.json \
  --seed 42 \
  --device auto
```

Verify:

```bash
cat outputs/container-train/metrics.json
```

## Import the Image into the GPU-Capable Local Cluster

```bash
mkdir -p build
docker save kubeflow-by-doing/train:local > build/train-image.tar
sudo microk8s ctr image import build/train-image.tar
```

Verify with a one-off pod:

```bash
kubectl run train-image-smoke-test \
  --image=kubeflow-by-doing/train:local \
  --restart=Never \
  --image-pull-policy=Never \
  -- --help
```

Inspect logs:

```bash
kubectl logs pod/train-image-smoke-test
```

Cleanup:

```bash
kubectl delete pod train-image-smoke-test --ignore-not-found
```

## GPU Image Note

Chapter 3 assumes the GPU-capable `MicroK8s` path is available for meaningful PyTorch-on-Kubernetes work.

The image shown here still uses a CPU-oriented Python base image because it is the smallest packaging step that proves the CLI, dependencies, and entrypoint are wired correctly.

Once the packaging path is stable, you can swap to a CUDA-enabled PyTorch base image without changing the overall chapter structure.

## Common Problems

### `uv.lock` does not exist

Run:

```bash
uv sync
```

Then rebuild.

### `kbd` is not found inside the container

Check that:

- `[project.scripts]` exists in `pyproject.toml`
- the package is installed inside the image
- `src/` is copied into the image

### Container works locally but pod fails

The image probably was not imported into the active cluster:

```bash
docker save kubeflow-by-doing/train:local > build/train-image.tar
sudo microk8s ctr image import build/train-image.tar
```

Then inspect pod events:

```bash
kubectl describe pod train-image-smoke-test
```

## Cleanup

```bash
rm -rf outputs/container-train
kubectl delete pod train-image-smoke-test --ignore-not-found
```

Optionally:

```bash
docker rmi kubeflow-by-doing/train:local
```

## Acceptance Criteria

You are done when:

- `Dockerfile` exists
- `docker build -t kubeflow-by-doing/train:local .` succeeds
- containerized training writes `model.pt`
- containerized evaluation writes `metrics.json`
- the image is imported into the GPU-capable local cluster
- a Kubernetes pod can run `kbd --help` from the image

## References

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/)
- [MicroK8s local image import](https://microk8s.io/docs/registry-images)
- [PyTorch Docker images](https://hub.docker.com/r/pytorch/pytorch)

## Next Step

Continue with [Train in Kubeflow](06-train-in-kubeflow.md).
