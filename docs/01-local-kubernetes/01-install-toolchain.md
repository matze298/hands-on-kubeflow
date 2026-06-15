# Install the Local Toolchain

This page installs the command-line tools used throughout the tutorial and syncs this repository's Python environment.

The repository bootstrap script is built on `uv` primitives: `uv init` for project creation in a fresh clone, `uv lock` for dependency resolution, and `uv sync` for installing the locked environment.

The goal is not to install every possible MLOps tool. The goal is to create a small, modern local toolchain that can build, run, and debug Kubernetes-native ML workflows.

## What You Will Install

Core tools:

- Docker or a compatible container runtime
- NVIDIA driver and NVIDIA Container Toolkit
- `kubectl`
- `kind`
- `minikube`
- `helm`
- `kustomize`
- `uv`
- `ruff`
- `ty`
- `pytest`
- `mkdocs-material`
- `prek`

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

For this repository:

```bash
./setup.py
```

If you already have a matching `pyproject.toml` in a different clone:

```bash
uv sync --all-groups
```

Verify:

```bash
uv run python --version
uv run ruff --version
uv run ty --version
uv run pytest --version
uv run mkdocs --version
uv run marimo --version
uv run prek --version
```

## Install Docker

Install Docker from Ubuntu packages:

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo usermod -aG docker "$USER"
```

Log out and back in, or start a new shell, so the `docker` group change takes effect.

Install the NVIDIA Container Toolkit for Docker:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## Install `kubectl`

On Ubuntu, install `kubectl` from the Kubernetes APT repository:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.32/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.32/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl
```

On other systems, use your operating system package manager or the official Kubernetes installation instructions.

Verify:

```bash
kubectl version --client
```

You do not need a cluster yet. This only verifies that the client is installed.

## Install `kind`

`kind` runs Kubernetes clusters inside containers. It is a good starter cluster for the first Kubernetes exercises because it is disposable, scriptable, and widely used for Kubernetes testing.

On Ubuntu, install `kind` as a standalone binary:

```bash
curl -Lo kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-linux-amd64
chmod +x kind
sudo mv kind /usr/local/bin/kind
```

Verify:

```bash
kind version
```

## Install `minikube` for the GPU-Capable Local Kubernetes Path on WSL2

Keep `kind` available for the starter Kubernetes path and as the fallback if you do not have the GPU-capable local setup.

`minikube` with the Docker driver is the tutorial's GPU-capable local ML platform on WSL2. Install it instead of trying to force GPU passthrough through the `kind` starter cluster.

On Ubuntu, install the current `minikube` package:

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube_latest_amd64.deb
sudo dpkg -i minikube_latest_amd64.deb
rm minikube_latest_amd64.deb
```

Verify:

```bash
minikube version
```

Use minikube v1.32.0 or newer for the Docker-driver GPU path.

Before using minikube for GPU workloads, verify Docker can see the GPU from inside WSL2:

```bash
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi
```

If this fails, fix Docker GPU support before creating the minikube cluster. Kubernetes GPU scheduling depends on the same runtime path.

You do not need to create the minikube cluster yet. The next page creates a named profile with the Docker driver and GPU flags.

For a quick client check:

```bash
minikube status -p kubeflow-gpu || true
```

## Install `helm`

We use Helm later when installing Kubernetes applications.

On Ubuntu, install `helm` with:

```bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

```bash
helm version
```

## Install `kustomize`

We use Kustomize later for environment-specific overlays.

On Ubuntu, install `kustomize` as a standalone binary:

```bash
curl -Lo kustomize.tar.gz https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v5.8.1/kustomize_v5.8.1_linux_amd64.tar.gz
tar -xzf kustomize.tar.gz
sudo mv kustomize /usr/local/bin/kustomize
```

If you are on a different architecture, use the matching asset from the official Kustomize release page and keep the version pinned intentionally.

```bash
kustomize version
```

## Verify Docker and GPU Support

```bash
docker version
docker run --rm hello-world
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
uv --version
uv run ruff --version
uv run ty --version
```

For GPU readiness:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu24.04 nvidia-smi
```

When you set up the GPU-capable `minikube` path:

```bash
minikube status -p kubeflow-gpu
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

### `uv run mkdocs --version` fails

That usually means the docs dependency group was not synced.

Run:

```bash
./setup.py
```

If you are working in a different clone with the same layout, make sure the docs group is installed before continuing.

### `uv run prek --version` fails

That usually means the dev dependency group was not synced, or the bootstrap script has not installed the hook tooling yet.

Run:

```bash
./setup.py
```

If the command still fails, verify that `prek` is listed in `pyproject.toml` and that `uv sync --all-groups` completed successfully.

## Cleanup

No cleanup is needed for this page.

## What You Learned

You installed and verified the local tooling needed to build a Kubernetes-native ML workflow.

## References

- [uv documentation](https://docs.astral.sh/uv/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [ty documentation](https://docs.astral.sh/ty/)
- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [minikube NVIDIA GPU tutorial](https://minikube.sigs.k8s.io/docs/tutorials/nvidia_gpu/)
- [Kubernetes kubectl documentation](https://kubernetes.io/docs/reference/kubectl/)
- [NVIDIA Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [CUDA on WSL user guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)

## Acceptance Criteria

You are done when:

- `docker run --rm hello-world` succeeds
- `kubectl version --client` works
- `kind version` works
- `minikube version` works
- `uv --version` works
- `uv run ruff --version` works inside the repo
- `uv run prek --version` works inside the repo
- `docker run --rm --gpus all ... nvidia-smi` succeeds, or you have documented why GPU support is not available on this machine

## Next Step

Continue with [Create a Local Kubernetes Cluster](02-create-local-cluster.md).
