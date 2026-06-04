# Syllabus

## Course Goal

Build a local, GPU-aware Kubeflow learning environment that turns a normal PyTorch workflow into a reproducible, containerized, Kubernetes-native MLOps workflow.

The tutorial starts from a local Linux or WSL2 development machine with an NVIDIA GPU and expands later to STACKIT, cloud object storage, CI/CD, and production-style deployment.

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
```

## Expansion Tracks

```text
7. STACKIT Expansion
8. Generic Cloud Expansion
9. CI/CD Expansion
```

## 0. Orientation

### 0.1 Syllabus

Define what the tutorial teaches, what it skips, and how the course is structured.

### 0.2 Reader Contract

Define the intended reader.

The reader knows Python, PyTorch, and basic deep learning. The reader may be new to Kubernetes and Kubeflow.

### 0.3 Authoring Contract

Define how chapters are generated, refined, validated, and kept concise.

### 0.4 Course Architecture

Show the local-first, GPU-aware architecture and explain how later expansion chapters fit in.

## 1. Local Kubernetes

### 1.1 Install the Local Toolchain

Install and verify:

- Docker or compatible container runtime
- NVIDIA driver and container runtime support
- `kubectl`
- `kind` or `k3d`
- `helm`
- `kustomize`
- `uv`
- `ruff`
- `ty`
- `pytest`
- `mkdocs-material`

### 1.2 Create a Local Kubernetes Cluster

Create a disposable local Kubernetes cluster for the tutorial.

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

### 2.3 Components, Parameters, and Artifacts

Turn a toy ML workflow into pipeline components.

Pipeline:

```text
generate_data → train_model → evaluate_model
```

### 2.4 Reusable Components

Refactor components so that they can be tested and reused.

Focus:

- component boundaries
- container images
- typed inputs and outputs
- local testing before pipeline execution

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

### 3.3 Containerize Training

Build a training image that can run locally and in Kubernetes.

Focus:

- reproducible image builds
- GPU-capable image variant
- CPU fallback where practical
- loading local images into the local cluster

### 3.4 Train a PyTorch Model Locally

Create a simple image classification training script.

The ML code is intentionally minimal. The focus is the workflow.

### 3.5 Train the Model in Kubeflow

Run the same training logic as a Kubeflow component.

Pipeline:

```text
prepare_data → train → evaluate
```

### 3.6 Add Evaluation Gates

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

### 5.2 Deploy the Server to Kubernetes

Deploy the model server into the local cluster.

Focus:

- Deployment
- Service
- ConfigMap
- Secret
- port forwarding

### 5.3 Connect Pipeline to Serving

Connect model promotion to the served model URI.

Focus:

- simple redeploy pattern
- smoke test endpoint
- local rollout

### 5.4 KServe Preview

Introduce KServe conceptually and optionally.

KServe is not required for the core path, but the reader should understand where it fits.

## 6. Local GPU

### 6.1 Verify NVIDIA Container Support

Verify that the GPU is visible inside containers.

### 6.2 Expose GPU to Local Kubernetes

Install or configure the necessary local Kubernetes GPU support.

Focus:

- NVIDIA device plugin
- GPU resource requests
- scheduling
- common failure modes

### 6.3 Run a GPU Test Job

Run `nvidia-smi` and a tiny PyTorch CUDA test inside the cluster.

### 6.4 Run GPU Training in Kubeflow

Run the training component with GPU resources.

Focus:

- accelerator resource requests
- CPU fallback
- image compatibility
- debugging failed GPU scheduling

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

### 9.1 Build Images in CI

Build training and serving images automatically.

### 9.2 Compile Pipelines in CI

Validate KFP pipeline definitions on every pull request.

### 9.3 Trigger Pipeline Runs

Submit pipeline runs from CI or scripts.

### 9.4 GitOps Promotion

Promote model versions through Git-based deployment changes.

## 10. Capstone

Build the final end-to-end local workflow:

```text
ingest_data
  ↓
validate_data
  ↓
train_model
  ↓
evaluate_model
  ↓
register_or_record_model
  ↓
deploy_model
  ↓
smoke_test_endpoint
```

The capstone should run locally first and then point to STACKIT/cloud expansion steps.
