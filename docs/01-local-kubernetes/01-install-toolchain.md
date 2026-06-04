# Install the Local Toolchain

This page installs the command-line tools used throughout the tutorial.

The goal is not to install every possible MLOps tool. The goal is to create a small, modern local toolchain that can build, run, and debug Kubernetes-native ML workflows.

## What You Will Install

Core tools:

- Docker or a compatible container runtime
- NVIDIA driver and NVIDIA Container Toolkit
- `kubectl`
- `kind`
- `helm`
- `kustomize`
- `uv`
- `ruff`
- `ty`
- `pytest`
- `mkdocs-material`

Optional but recommended:

- `marimo`
- `jq`
- `yq`
- `watch`
- `stern` or `kubetail`

## Why This Matters

Kubeflow workloads are containerized Kubernetes workloads.

The basic development loop is:

```text
write code
  ↓
build container image
  ↓
run image locally
  ↓
load or push image
  ↓
run workload in Kubernetes
  ↓
inspect logs, events, and artifacts
```

If this local toolchain is unreliable, Kubeflow will feel unreliable too.

## Prerequisites

This tutorial assumes:

```text
Linux or WSL2 Linux
NVIDIA GPU
recent NVIDIA driver
Docker or Docker Desktop with WSL2 integration
```

For WSL2, first verify that the GPU is visible from inside the Linux environment:

```bash
nvidia-smi
```

If that does not work, fix the WSL2/NVIDIA setup before continuing.

## Install `uv`

`uv` is the default Python project and dependency manager for this tutorial.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your shell or source the environment file shown by the installer.

Verify:

```bash
uv --version
```

## Install Python Tools

Inside the tutorial repository, initialize or sync the Python environment with `uv`.

For a new repo:

```bash
uv init --package kubeflow-by-doing
uv add --dev ruff ty pytest mkdocs-material marimo
```

For an existing repo with `pyproject.toml`:

```bash
uv sync
```

Verify:

```bash
uv run python --version
uv run ruff --version
uv run ty --version
uv run pytest --version
uv run mkdocs --version
uv run marimo --version
```

## Install `kubectl`

Use your operating system package manager or the official Kubernetes installation instructions.

Verify:

```bash
kubectl version --client
```

You do not need a cluster yet. This only verifies that the client is installed.

## Install `kind`

`kind` runs Kubernetes clusters inside containers. It is a good default for local learning because it is disposable, scriptable, and widely used for Kubernetes testing.

Verify:

```bash
kind version
```

## Install `helm`

We use Helm later when installing Kubernetes applications.

```bash
helm version
```

## Install `kustomize`

We use Kustomize later for environment-specific overlays.

```bash
kustomize version
```

## Verify Docker

```bash
docker version
docker run --rm hello-world
```

## Verify NVIDIA Container Support

```bash
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi
```

If this fails, Kubernetes GPU scheduling will also fail later.

Common causes:

- NVIDIA driver is missing or too old
- NVIDIA Container Toolkit is not installed
- Docker Desktop WSL2 integration is not enabled
- WSL2 cannot see the GPU
- Docker was not restarted after installing NVIDIA Container Toolkit

## Verify the Toolchain

Run:

```bash
kubectl version --client
kind version
helm version
kustomize version
docker version
uv --version
uv run ruff --version
uv run ty --version
```

For GPU readiness:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi
```

## Common Problems

### `kubectl` says it cannot connect to a cluster

That is expected before creating the local cluster.

You only need `kubectl version --client` to work at this stage.

### `docker run hello-world` fails

Fix Docker before continuing. `kind` depends on Docker or another supported container runtime.

### `docker run --gpus all ... nvidia-smi` fails

Fix NVIDIA container support before attempting GPU workloads in Kubernetes.

For WSL2, first check:

```bash
nvidia-smi
```

Then check Docker Desktop WSL2 integration and NVIDIA Container Toolkit support.

### `uv run ty --version` fails

`ty` is young tooling. If it is temporarily unavailable or changes its CLI, keep the tutorial structure but document the exact version used in `pyproject.toml`.

Do not replace the type-checking section with legacy defaults unless needed for compatibility.

## Cleanup

No cleanup is needed for this page.

## What You Learned

You installed and verified the local tooling needed to build a Kubernetes-native ML workflow.

## References

- [uv documentation](https://docs.astral.sh/uv/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [ty documentation](https://docs.astral.sh/ty/)
- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [Kubernetes kubectl documentation](https://kubernetes.io/docs/reference/kubectl/)
- [NVIDIA Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [CUDA on WSL user guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)

## Acceptance Criteria

You are done when:

- `docker run --rm hello-world` succeeds
- `kubectl version --client` works
- `kind version` works
- `uv --version` works
- `uv run ruff --version` works inside the repo
- `docker run --rm --gpus all ... nvidia-smi` succeeds, or you have documented why GPU support is not available on this machine

## Next Step

Continue with [Create a Local Kubernetes Cluster](02-create-local-cluster.md).
