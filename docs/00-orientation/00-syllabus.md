# Syllabus

## Course Goal

Build a local, GPU-aware Kubeflow learning environment that turns a normal PyTorch workflow into a reproducible, containerized, Kubernetes-native MLOps workflow.

The tutorial starts from a local Linux or WSL2 development machine with an NVIDIA GPU. Chapter 1 begins with `kind` for the first Kubernetes basics, then the core ML path uses `minikube` as the default local Kubernetes platform. The course expands later to STACKIT, cloud object storage, and CI/CD, then points to production serving and full Kubeflow platform operations as follow-up topics.

This is a build-along tutorial: the chapter pages show the files, commands, and manifests to create, and the reader is expected to build the repository state while following along.

## Core Learning Path

```text
0. Orientation
1. Local Kubernetes
2. Kubeflow Pipelines
3. Local ML Workflow
4. Artifacts and Tracking
5. Local Serving
6. Local GPU
10. Capstone
11. Conclusion and Future Reading
```

## Expansion Tracks

```text
7. STACKIT Expansion
8. Generic Cloud Expansion
9. CI/CD Expansion
```

## Optional Add-On

```text
12. Flyte Instead of Kubeflow Pipelines
13. FAQ
14. KServe Add-On
```

## 0. Orientation

### 0.1 Syllabus

Define what the tutorial teaches, what it skips, and how the course is structured.

### 0.2 Reader Contract

Define the intended reader.

The reader knows Python, PyTorch, and basic deep learning. The reader may be new to Kubernetes and Kubeflow.

### 0.3 Course Architecture

Show the local-first, GPU-aware architecture and explain how later expansion chapters fit in.

## 1. Local Kubernetes

### 1.1 Install the Local Toolchain

Install and verify:

- Docker or compatible container runtime
- NVIDIA driver and container runtime support
- `kubectl`
- `kind` for the starter cluster
- `minikube` for the default GPU-capable local ML path
- `helm`
- `kustomize`
- `uv`
- `ruff`
- `ty`
- `pytest`
- `mkdocs-material`

### 1.2 Create a Local Kubernetes Cluster

Create a disposable local Kubernetes cluster for the starter Kubernetes path, then switch to the GPU-capable `minikube` cluster for the ML chapters.

Focus:

- cluster creation
- namespaces
- local image loading
- port forwarding
- cleanup

### 1.3 Run the First Kubernetes Job

Run a tiny Python workload as a Kubernetes Job.

Motivation:

A training run is conceptually similar to a Kubernetes Job: start, run, write outputs, finish.

### 1.4 Debug Kubernetes Workloads

Learn the commands that will be reused throughout the tutorial:

- `kubectl get`
- `kubectl describe`
- `kubectl logs`
- `kubectl get events`
- debugging pending pods
- debugging image pull errors
- debugging failed jobs

## 2. Kubeflow Pipelines

### 2.1 Install Kubeflow Pipelines Locally

Install standalone Kubeflow Pipelines into the local cluster.

Focus:

- KFP only, not full Kubeflow
- UI access via port forwarding
- verifying that KFP is healthy

### 2.2 First Pipeline

Create and run a minimal KFP pipeline.

Focus:

- KFP SDK
- pipeline compilation
- pipeline submission
- inspecting runs in the UI

### 2.3 Run a Pipeline from Python

Submit a compiled pipeline run from a local Python script.

Focus:

- KFP client setup
- endpoint configuration
- repeatable scripted submissions
- mapping submitted runs back to the UI

### 2.4 Components, Parameters, and Artifacts

Turn a toy ML workflow into pipeline components.

Pipeline:

```text
generate_data → train_model → evaluate_model
```

### 2.5 Reusable Components

Refactor components so that they can be tested and reused.

Focus:

- component boundaries
- container images
- typed inputs and outputs
- local testing before pipeline execution

### 2.6 Debugging KFP Runs

Debug failed pipeline steps by mapping KFP state back to Kubernetes pods, logs, and events.

## 3. Local ML Workflow

### 3.1 Project Structure

Create the production-shaped tutorial repository.

Recommended layout:

```text
kubeflow-by-doing/
├── docs/
├── src/
├── components/
├── pipelines/
├── manifests/
├── infra/
├── examples/
├── tests/
├── pyproject.toml
└── mkdocs.yml
```

### 3.2 Modern Python Tooling

Set up:

- `uv`
- `ruff`
- `ty`
- `pytest`
- task commands
- lockfile-based reproducibility

### 3.3 Train a PyTorch Model Locally

Create a simple image classification training script.

The ML code is intentionally minimal. The focus is the workflow.

### 3.4 Add Tests and Quality Checks

Add local checks before the workflow moves into containers and Kubeflow.

Focus:

- unit tests
- linting and formatting
- type checking
- fast feedback before image builds

### 3.5 Containerize Training

Build a training image that can run locally and in Kubernetes.

Focus:

- reproducible image builds
- Docker cache mounts for dependency reuse
- GPU-capable image variant
- CPU fallback where practical
- loading local images into the local cluster

### 3.6 Train the Model in Kubeflow

Run the same training logic as a Kubeflow component.

Pipeline:

```text
prepare_data → train → evaluate
```

### 3.7 Add Evaluation Gates

Only promote a model if its evaluation metric passes a threshold.

Focus:

- metrics as control flow
- conditional execution
- promotion decisions

## 4. Artifacts and Tracking

### 4.1 Install Local Object Storage

Install MinIO as local S3-compatible storage.

Focus:

- buckets
- credentials
- Kubernetes Secrets
- port forwarding
- artifact paths

### 4.2 Define Artifact Layout

Define a portable layout:

```text
s3://kubeflow-by-doing/
├── datasets/
├── models/
├── metrics/
├── reports/
└── predictions/
```

### 4.3 Add Experiment Tracking

Add MLflow or a similarly lightweight local tracking setup.

Focus:

- parameters
- metrics
- artifacts
- links between KFP runs and tracking runs

### 4.4 Trace Lineage

Record:

- Git SHA
- image tag
- dataset URI
- model URI
- metrics URI
- KFP run ID
- tracking run ID

## 5. Local Serving

### 5.1 Build a FastAPI Model Server

Serve the trained model through a simple API.

Focus:

- loading model artifacts
- health endpoint
- prediction endpoint
- local testing

### 5.2 Containerize Serving

Build a serving image for the FastAPI model server.

Focus:

- serving Dockerfile
- Docker cache mounts for dependency reuse
- local container test
- image loading into the local cluster

### 5.3 Deploy the Server to Kubernetes

Deploy the model server into the local cluster.

Focus:

- Deployment
- Service
- ConfigMap
- Secret
- port forwarding

### 5.4 Connect Pipeline to Serving

Connect model promotion to the served model URI.

Focus:

- simple redeploy pattern
- smoke test endpoint
- local rollout

### 5.5 KServe Preview

Introduce KServe conceptually and optionally.

KServe is not required for the core path, but the reader should understand where it fits.

The hands-on KServe work appears later as an optional add-on, after the core serving and capstone path are complete.

## 6. Local GPU

### 6.1 Confirm the GPU Path

Briefly verify that the local `minikube` setup still exposes GPU resources to containers and pods.

Focus:

- container-level GPU check
- Kubernetes-level GPU check
- failure modes that matter for the tutorial

### 6.2 Run a CUDA Smoke Test in the Cluster

Run a tiny PyTorch CUDA workload inside Kubernetes.

Focus:

- `nvidia.com/gpu` resource requests
- image compatibility
- scheduling and readiness

### 6.3 Make KFP GPU-Aware

Run the training component with GPU resources inside Kubeflow.

Focus:

- accelerator resource requests
- CPU fallback when GPU is unavailable
- component and image compatibility
- debugging failed GPU scheduling in KFP

## 7. STACKIT Expansion

### 7.1 STACKIT Architecture

Map local components to STACKIT services.

```text
local Kubernetes        → STACKIT Kubernetes Engine
local MinIO             → STACKIT object storage or self-hosted MinIO
local image loading     → container registry
local GPU               → GPU node pool
port forwarding         → ingress or load balancer
```

### 7.2 Create a STACKIT Kubernetes Cluster

Create and access a STACKIT SKE cluster.

### 7.3 Deploy Kubeflow Pipelines on STACKIT

Move the local KFP deployment to SKE.

### 7.4 Configure Object Storage

Replace local MinIO with STACKIT object storage or another S3-compatible backend.

### 7.5 Add GPU Node Pool

Run GPU training in the cloud cluster.

### 7.6 Cost Control and Cleanup

Make teardown explicit.

## 8. Generic Cloud Expansion

Compare managed Kubernetes providers and explain what changes when moving away from local infrastructure.

Focus:

- storage classes
- load balancers
- object storage
- container registry
- GPU availability
- cost traps
- cleanup

## 9. CI/CD Expansion

### 9.1 CI Checks

Run the same local quality gates in CI.

Focus:

- formatting
- linting
- type checking
- tests
- docs build

### 9.2 Build Images in CI

Build training and serving images automatically.

### 9.3 Compile Pipelines in CI

Validate KFP pipeline definitions on every pull request.

### 9.4 Trigger Pipeline Runs

Submit pipeline runs from CI or scripts.

### 9.5 GitOps Promotion

Promote model versions through Git-based deployment changes.

### 9.6 Security and Maintenance

Keep secrets out of the repository and gate expensive or production-affecting actions.

## 10. Capstone

Use the final end-to-end local workflow as a guided assessment:

```text
ingest_data
  ↓
validate_data
  ↓
train_model
  ↓
evaluate_model
  ↓
read_accuracy
  ↓
promote_model
  ↓
write_lineage
  ↓
record_or_register_model
  ↓
deploy_model, if enabled
  ↓
smoke_test_model, if deployed
```

The capstone should run locally first and then point to STACKIT/cloud expansion steps. Readers should build the final files themselves from the contract, requirements, hints, and verification checks; complete reference implementations stay behind spoiler blocks.

## 11. Conclusion and Future Reading

Summarize the platform shape built by the tutorial and point readers to the next advanced topics.

Focus:

- when to use this Kubeflow/Kubernetes path instead of a managed ML platform
- KServe production serving
- inference runtime optimization
- AI gateways and inference-aware routing
- Kubeflow Hub / Model Registry
- Katib hyperparameter tuning
- Kubeflow Trainer and distributed training
- Ray / KubeRay for adjacent distributed Python workloads
- JobSet for multi-job distributed workloads
- Kueue batch and GPU scheduling
- Kubernetes Dynamic Resource Allocation
- Kubernetes AI platform conformance
- data versioning and reproducibility
- data quality frameworks
- Kubeflow Spark Operator for larger data processing
- Feast feature stores
- observability and drift monitoring
- GenAI observability standards
- image signing, provenance, and policy
- secret management and identity
- GitOps controllers
- GenAI application-layer tooling
- MCP and OWASP GenAI security

## 12. Optional Flyte Add-On

Translate the tutorial's train/evaluate workflow to Flyte after the core Kubeflow path is complete.

This add-on is not part of the required Kubeflow course path. It is a focused comparison track for readers who want to evaluate Flyte as an alternative workflow orchestrator.

### 12.0 Overview

Explain why Flyte is included, how it fits after the conclusion, and what the optional track covers.

### 12.1 Flyte Concepts vs KFP

Map KFP components, pipeline functions, artifacts, and compile/run habits to Flyte tasks, `TaskEnvironment`, typed task signatures, and local task execution.

### 12.2 Local Flyte Workflow

Create `flyte/kbd_flyte_workflow.py`, reuse the tutorial's existing train/evaluate functions, run the workflow locally with `uv run flyte`, and prepare the task environment for a later minikube backend run.

### 12.3 Artifacts, Resources, and Secrets

Explain why inline model payloads are only a teaching shortcut, then cover durable file/directory artifacts, explicit object storage paths, CPU/GPU task environments, images, secrets, caching, and promotion records.

### 12.4 Remote Backend and Tradeoffs

Explain what changes when Flyte moves from local execution to a remote backend, including Kubernetes task pods, images, artifact storage, identity, GPU scheduling, observability, CI/CD impact, and the final Flyte-vs-KFP decision.

### 12.5 Run Flyte on minikube

Install a local Flyte backend into the tutorial's `minikube` cluster, build a Flyte task image, load it into the minikube profile, deploy the Flyte environment, and submit the workflow so it runs as Kubernetes task pods.

## 13. FAQ

Collect practical recovery procedures for common local tutorial problems.

Focus:

- resetting tutorial namespaces without rebuilding the whole cluster
- hard-resetting the local `minikube` cluster when the platform itself is unhealthy
- restarting or reinstalling standalone Kubeflow Pipelines
- linking back to the setup chapters instead of duplicating the full install flow
