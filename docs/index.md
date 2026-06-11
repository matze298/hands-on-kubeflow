# Kubeflow by Doing

A local-first, GPU-aware, hands-on tutorial for learning Kubeflow, Kubernetes-native machine learning workflows, and practical MLOps.

The tutorial is written for readers who already know Python, PyTorch, and basic deep learning, but who want to move from ML code to reproducible, containerized, Kubernetes-native MLOps workflows.

The core path starts with `kind` for the first Kubernetes basics and then treats `MicroK8s` on WSL2 as the default local ML platform. Cloud, STACKIT, full Kubeflow, production serving, and CI/CD are introduced later as expansion chapters. A final optional add-on compares the same workflow with Flyte instead of Kubeflow Pipelines, and the FAQ collects reset procedures for local tutorial environments.

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
3. Start the site locally:

```bash
./setup.py
uv run mkdocs serve
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
- capstone
  - ingest and validate data explicitly
  - use the full local Kubeflow workflow as a guided end-to-end test
  - keep complete reference implementations behind spoiler blocks
  - keep artifacts durable outside pod filesystems
  - map the same pipeline to STACKIT or another cloud provider
- conclusion and future reading
  - summarize the platform shape you built
  - explain which advanced Kubeflow and MLOps components to study next
  - link to official references for KServe, inference runtimes, AI gateways, Kubeflow Hub / Model Registry, Katib, Trainer, Ray / KubeRay, JobSet, Kueue, DRA, AI conformance, data versioning, data quality, Spark Operator, Feast, observability, GenAI telemetry, policy, GitOps controllers, GenAI application tooling, MCP, and LLM security
- optional Flyte add-on
  - translate the train/evaluate workflow to Flyte tasks
  - map Flyte concepts against KFP concepts
  - run a local Flyte workflow with `uv run flyte`
  - deploy a Flyte backend into MicroK8s for a Kubernetes-backed comparison
  - compare artifact, resource, secret, and backend tradeoffs
  - keep the add-on outside the required Kubeflow path
- FAQ
  - reset local `MicroK8s` safely
  - reset standalone Kubeflow Pipelines
  - choose between namespace, KFP, and full cluster resets
