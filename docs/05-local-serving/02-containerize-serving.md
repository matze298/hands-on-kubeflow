# Containerize Serving

This page turns the FastAPI model server into a container image.

## What You Will Build

You will create:

```text
Dockerfile.serve
```

and build:

```text
kubeflow-by-doing/serve:local
```

## Why This Matters

The model server must run in Kubernetes.

That means it needs the same discipline as the training workload:

```text
works locally
  ↓
works in a container
  ↓
works in Kubernetes
```

## Create `Dockerfile.serve`

Create `Dockerfile.serve` in the repository root:

```dockerfile
# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

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

ENV KBD_MODEL_PATH=/models/model.pt
ENV KBD_SERVE_DEVICE=cpu

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "kubeflow_by_doing.serve:app", "--host", "0.0.0.0", "--port", "8000"]
```

!!! note

    This image expects the model file to be mounted at `/models/model.pt`. In Kubernetes, we will use an init container to download the model from MinIO into that path.

The two-step `uv sync` keeps dependency downloads in a reusable layer and only reinstalls the local project after the source files change.

`# syntax=docker/dockerfile:1.7` enables the Dockerfile features used below, including the `RUN --mount=type=cache` cache mount.

## Build the Image

```bash
docker build -f Dockerfile.serve -t kubeflow-by-doing/serve:local .
```

Verify:

```bash
docker images | grep kubeflow-by-doing
```

## Run the Container Locally

Make sure a model exists:

```bash
mkdir -p outputs/local-train

uv run kbd train-model \
  --output-dir outputs/local-train \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --device cpu
```

Run the server container:

```bash
docker run --rm \
  -p 8000:8000 \
  -v "$PWD/outputs/local-train:/models:ro" \
  kubeflow-by-doing/serve:local
```

## Check Health

In another terminal:

```bash
curl http://localhost:8000/healthz
```

## Send a Prediction

```bash
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

## Load the Image into the Default Cluster

If you are on the default `MicroK8s` path, load the image with:

```bash
mkdir -p build
docker save kubeflow-by-doing/serve:local > build/serve-image.tar
sudo microk8s ctr image import build/serve-image.tar
```

If you are on the `kind` fallback path, load the image with:

```bash
kind load docker-image kubeflow-by-doing/serve:local --name kubeflow-by-doing
```

## Optional GPU Serving Note

The local serving path uses CPU by default.

That is intentional. Most small online inference paths are easier to debug on CPU first.

GPU serving can be added later by:

- using a CUDA/PyTorch base image
- setting `KBD_SERVE_DEVICE=cuda`
- requesting `nvidia.com/gpu: 1` in the pod
- validating latency and utilization

Do not add GPU serving until CPU serving is stable.

## Common Problems

### Container cannot find `/models/model.pt`

Check the volume mount:

```bash
-v "$PWD/outputs/local-train:/models:ro"
```

and verify:

```bash
ls -lh outputs/local-train/model.pt
```

### Server cannot import package code

Check that the Dockerfile copies `src/` and installs the project.

### Port already in use

Use another local port:

```bash
docker run --rm \
  -p 18000:8000 \
  -v "$PWD/outputs/local-train:/models:ro" \
  kubeflow-by-doing/serve:local
```

Then call:

```bash
curl http://localhost:18000/healthz
```

## Cleanup

Stop the container with `Ctrl+C`.

Optionally remove the image:

```bash
docker rmi kubeflow-by-doing/serve:local
```

## Acceptance Criteria

You are done when:

- `Dockerfile.serve` exists
- `docker build -f Dockerfile.serve -t kubeflow-by-doing/serve:local .` succeeds
- the serving container starts locally
- `/healthz` succeeds
- `/predict` succeeds
- the serving image is loaded into `MicroK8s`, or into `kind` if that is your fallback path

## References

- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
- [uv Docker integration guide](https://docs.astral.sh/uv/guides/integration/docker/)
- [FastAPI deployment docs](https://fastapi.tiangolo.com/deployment/)

## Next Step

Continue with [Deploy to Kubernetes](03-deploy-to-kubernetes.md).
