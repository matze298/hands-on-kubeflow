# Kubeflow by Doing

A local-first, GPU-aware, hands-on tutorial for learning Kubeflow, Kubernetes-native machine learning workflows, and practical MLOps.

The tutorial is written for readers who already know Python, PyTorch, and basic deep learning, but who want to move from ML code to reproducible, containerized, Kubernetes-native MLOps workflows.

The core path starts with `kind` for the first Kubernetes basics and then treats `MicroK8s` on WSL2 as the default local ML platform. Cloud, STACKIT, full Kubeflow, production serving, and CI/CD are introduced later as expansion chapters.

## What You Will Build

By the end of the core tutorial, you will have built a local MLOps environment:

```text
Linux / WSL2 dev machine with NVIDIA GPU
  ↓
local Kubernetes
  ↓
Kubeflow Pipelines
  ↓
containerized PyTorch training
  ↓
local object storage
  ↓
evaluation gate
  ↓
local model serving
```

The ML workload is intentionally simple. The point is not to teach deep learning from scratch, but to make the MLOps workflow concrete.

## Start Here

1. Read the [Syllabus](00-orientation/00-syllabus.md).
2. Read the [Reader Contract](00-orientation/01-reader-contract.md).
3. Read the [Authoring Contract](00-orientation/02-authoring-contract.md).
4. Start the site locally:

```bash
uvx mkdocs-material
mkdocs serve
```

## Tutorial Style

Each chapter should be concise, practical, and reproducible.

The default chapter pattern is:

1. motivate the concept
2. build something concrete
3. verify the result
4. debug common failures
5. link to deeper references
6. define acceptance criteria

We explain what is likely unknown to an ML engineer moving into MLOps. We do not explain basic Python, PyTorch, or deep learning mechanics unless they affect the Kubeflow workflow.

## Course Path

The first hands-on section is [Local Kubernetes](01-local-kubernetes/00-overview.md).

It establishes the local environment, the cluster, the first Kubernetes job, the debugging loop, and GPU readiness before the tutorial moves on to Kubeflow Pipelines.

The rest of the path expands that baseline into:

- Kubeflow Pipelines
  - install standalone KFP locally
  - compile and run the first pipeline
  - submit pipeline runs from Python
  - use parameters, artifacts, and metrics
  - split workflow logic into reusable components
  - debug failed runs with Kubernetes tooling
- the local ML workflow
  - create a clean project structure under `src/`, `components/`, `pipelines/`, and `tests/`
  - configure modern Python tooling with `uv`, `ruff`, `ty`, and `pytest`
  - build a local training and evaluation CLI
  - add tests and local quality gates before containerization
  - containerize the training workflow
  - wrap the image as Kubeflow components
  - add a simple metric-based evaluation gate
- artifacts and tracking
  - add MinIO-backed object storage
  - define a portable artifact layout
  - add MLflow experiment tracking
  - write an explicit lineage record
- local serving
  - build a FastAPI model server
  - containerize it
  - deploy it to Kubernetes
  - connect promotion to a smoke test
  - preview KServe as the later expansion path
- local GPU-specific work
  - verify the GPU path
  - run a CUDA smoke test in the cluster
  - make KFP training GPU-aware
  - debug GPU scheduling failures
- STACKIT expansion
  - map the local workflow to STACKIT Kubernetes Engine
  - connect `kubectl` to SKE
  - push images to a registry reachable by the cluster
  - replace MinIO with STACKIT Object Storage
  - run Kubeflow Pipelines on SKE
  - validate an optional GPU node pool
  - clean up cloud resources explicitly
- generic cloud expansion
  - define the portability model
  - structure provider overlays
  - manage cloud secrets and registry access
  - keep object storage portable
  - generalize GPU and node-pool setup
  - plan provider-neutral cleanup
  - finish with a provider checklist
- CI/CD
  - automate checks and docs validation
  - build and tag images in CI
  - compile pipelines from a clean checkout
  - optionally submit pipeline runs
  - represent promotion as Git-tracked state
  - keep secrets and expensive actions gated
