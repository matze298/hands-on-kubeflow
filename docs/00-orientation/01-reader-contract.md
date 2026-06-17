# Reader Contract

This page defines the intended reader and the assumptions that every chapter should follow.

## Intended Reader

This tutorial is written for:

- ML engineers
- deep learning engineers
- research engineers
- software engineers moving into MLOps
- platform-curious AI engineers who want to understand Kubeflow hands-on

The reader already knows how to train models in Python, but wants to understand how those workflows become reproducible, containerized, and Kubernetes-native.

## Assumed Background

We assume that the reader is comfortable with:

- Python development
- basic command-line usage
- Git
- basic Docker concepts
- PyTorch
- datasets and dataloaders
- model checkpoints
- train/validation/test splits
- evaluation metrics
- the general idea of experiment tracking and reproducibility

We briefly motivate these concepts when they appear, but we do not teach them from scratch.

When a topic is important but not central to Kubeflow, the chapter should include a short summary and links for further reading.

## Not Assumed

We do not assume that the reader already knows:

- Kubernetes
- Kubeflow
- Kubeflow Pipelines
- KServe
- Kubernetes-native model serving
- STACKIT
- managed Kubernetes operations
- Kubernetes storage and networking details

Kubernetes is one of the central learning goals of this tutorial. However, the tutorial should still avoid an abstract Kubernetes deep dive.

We explain Kubernetes concepts when they become necessary for the ML workflow.

## Kubernetes Learning Scope

The tutorial should explain:

- Pods
- Jobs
- Services
- Namespaces
- Secrets
- ConfigMaps
- PersistentVolumes and PersistentVolumeClaims
- resource requests and limits
- GPU resource scheduling
- port forwarding
- basic debugging with `kubectl`
- the relationship between Kubeflow components and Kubernetes workloads

The tutorial should not deeply explain unless needed:

- controller internals
- CNI plugins
- CSI internals
- Kubernetes scheduler implementation
- admission controllers
- service mesh theory
- advanced networking
- cluster administration beyond the tutorial needs

## Hardware Assumption

The core tutorial targets:

```text
Linux or WSL2 Linux development machine
NVIDIA GPU available
Docker or compatible container runtime
local Kubernetes
```

The GPU may be required for core ML-readiness, but chapters should still be designed so that small CPU-only fallback runs are possible where practical.

The GPU path should be treated as a first-class part of the local development setup, not only as a cloud expansion.

## Notebook Assumption

The tutorial should not use Jupyter notebooks in the core workflow.

If interactive exploration is helpful, prefer [marimo](https://docs.marimo.io/) because marimo notebooks are stored as Python files, are Git-friendly, and can be executed as scripts.

Notebooks are optional. The core workflow should use scripts, containers, and pipelines.

## Tooling Assumption

Use modern, current tooling by default.

Prefer:

- `uv` for Python project and dependency management
- `ruff` for linting and formatting
- `ty` for type checking, once suitable for the chapter's purpose
- `pytest` for tests
- `marimo` for notebook-like interactive exploration
- `mkdocs-material` for documentation
- `prek` for Git hook management
- Docker or a compatible container runtime
- `kubectl`, `helm`, and `kustomize` for Kubernetes work
- `kind` for the starter and CPU fallback Kubernetes path
- `k3s` for the default GPU-capable local ML path
- Kubeflow Pipelines v2 style APIs
- containerized components
- reproducible CLI entry points

Avoid defaulting to older stacks such as:

- ad-hoc `pip install` workflows
- `requirements.txt` as the primary dependency story
- `pylint`
- `black`
- `mypy`
- notebook-only workflows
- unversioned local scripts

Older tools may be mentioned only when useful for comparison or compatibility.
For Git hooks, prefer `prek` and the repository's `prek.toml` configuration instead of ad-hoc pre-commit setup.

## ML Code Assumption

The ML code should be intentionally boring.

The tutorial does not teach:

- neural network fundamentals
- backpropagation
- loss functions in detail
- tensor basics
- CNN internals
- basic PyTorch syntax
- state-of-the-art model design

The model exists to make the workflow real.

A small image classification pipeline is the default example. Semantic segmentation, object detection, or multimodal examples can appear later as advanced extensions.

## MLOps Assumption

We assume the reader understands why reproducibility and deployment matter, but may not have built a Kubernetes-native ML platform before.

The tutorial should explain MLOps concepts through the running example:

- artifacts
- metadata
- experiment tracking
- lineage
- model promotion
- model serving
- CI/CD
- cloud expansion

## Writing Style

The style should be:

```text
concise where the reader already knows the concept
medium-depth where the concept is likely new
hands-on throughout
verify-driven
debugging-aware
reference-linked
```

Each chapter should avoid long theoretical introductions.

Each chapter should answer:

1. Why does this concept matter for ML workflows?
2. What will we build?
3. How do we verify that it works?
4. What usually goes wrong?
5. Where can the reader go deeper?

## Reader Promise

The reader should never feel that the tutorial is teaching basic deep learning.

The reader should also never feel that Kubernetes is treated as magic.

The tutorial bridges the gap:

```text
ML engineer
  ↓
containerized workloads
  ↓
Kubernetes-native execution
  ↓
Kubeflow pipelines
  ↓
practical MLOps platform
```
