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

Then make the image available to the default GPU-capable `k3s` cluster from Chapter 1. If you are staying on the `kind` fallback path, load the image into that cluster instead.

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
# syntax=docker/dockerfile:1.7

FROM python:3.14-slim

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

This keeps the image invocation model simple and keeps dependency downloads in a reusable layer:

- the first `uv sync` installs the locked dependencies without the local project
- the second `uv sync` installs the local project after the source files are copied
- BuildKit cache mounts let `uv` reuse downloaded packages across rebuilds
- `# syntax=docker/dockerfile:1.7` enables the Dockerfile features used below, including the `RUN --mount=type=cache` cache mount

- `docker run ... train-model ...` expands to `uv run kbd train-model ...`
- KFP container components can reuse the image entrypoint and pass only CLI arguments

## Build the Image

```bash
docker build -t kubeflow-by-doing/train:local .
```

If you prefer a wrapper script, put the same command into `build_docker.sh` and run that file instead. A small POSIX shell wrapper is enough:

```sh
#!/usr/bin/env sh
set -eu

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

## Make the Image Available to the GPU-Capable Local Cluster

Building the image makes it available to your host Docker daemon. The default `k3s` path in this tutorial also uses Docker as its runtime, so locally built images are available to k3s pods without a separate image-load command.

Verify that Docker has the image:

```bash
docker images kubeflow-by-doing/train:local
```

If you are using the `kind` fallback path instead, `kind` has its own node image store. Load the image with:

```bash
kind load docker-image kubeflow-by-doing/train:local --name kubeflow-by-doing
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

Chapter 3 assumes the GPU-capable `k3s` path is available for meaningful PyTorch-on-Kubernetes work.

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

On the default k3s path, verify that the image exists in Docker and that the pod uses `--image-pull-policy=Never` or a non-remote local tag:

```bash
docker images kubeflow-by-doing/train:local
```

On the `kind` fallback path, the image probably was not imported into the active cluster. Run:

```bash
kind load docker-image kubeflow-by-doing/train:local --name kubeflow-by-doing
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
- the image is available to the GPU-capable local cluster
- a Kubernetes pod can run `kbd --help` from the image

## References

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/)
- [PyTorch Docker images](https://hub.docker.com/r/pytorch/pytorch)

## Next Step

Continue with [Train in Kubeflow](06-train-in-kubeflow.md).
