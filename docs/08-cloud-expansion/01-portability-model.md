# Portability Model

This page defines what portability means for this tutorial.

## The Core Idea

A Kubeflow workflow is portable when the **pipeline logic** is not tied to a specific cloud provider.

Provider details should live in:

```text
environment files
Kubernetes Secrets
image parameters
pipeline root configuration
infrastructure overlays
cleanup docs
```

not in:

```text
training code
evaluation code
pipeline control flow
model server logic
```

## What Stays the Same

The tutorial's core workflow stays the same:

```text
train
  ↓
evaluate
  ↓
promote if metrics pass
  ↓
write lineage
  ↓
optionally deploy / smoke test
```

The Python package stays the same:

```text
src/kubeflow_by_doing/
```

The artifact layout stays the same:

```text
s3://<bucket>/runs/<run_id>/
├── models/
├── metrics/
├── reports/
├── predictions/
└── lineage/
```

## What Changes

The provider overlay supplies:

```text
KUBECONFIG
container image names
registry credentials
object storage endpoint
object storage credentials
pipeline root
GPU availability
node pool labels or tolerations
cleanup commands
```

## Create `infra/cloud/README.md`

Create:

```bash
mkdir -p infra/cloud
```

Create `infra/cloud/README.md`:

```markdown
# Generic Cloud Expansion

This folder contains provider-neutral cloud expansion material.

The tutorial keeps pipeline code provider-neutral and moves provider-specific configuration into overlays.

## Core Rule

Do not hardcode cloud providers into pipeline logic.

Prefer:

- pipeline parameters
- Kubernetes Secrets
- environment overlays
- provider-specific docs

## Supported Provider Families

This chapter describes patterns for:

- AWS EKS
- Azure AKS
- Google GKE
- STACKIT SKE
- generic managed Kubernetes

## Stable Interfaces

The tutorial expects these secret keys where possible:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
KBD_S3_ENDPOINT_URL
KBD_ARTIFACT_BUCKET
MLFLOW_S3_ENDPOINT_URL
MLFLOW_TRACKING_URI
MLFLOW_EXPERIMENT_NAME
```

Even on non-AWS providers, these names are acceptable when using S3-compatible APIs.
```

## Create `infra/cloud/env.example`

```bash
# Generic cloud provider selection
export KBD_CLOUD_PROVIDER="<aws|azure|gcp|stackit|generic>"
export KBD_CLUSTER_NAME="<cluster-name>"
export KBD_REGION="<region>"
export KUBECONFIG="$PWD/.kube/<provider>-kubeconfig.yaml"

# Images
export KBD_TRAIN_IMAGE="<registry>/<namespace>/kubeflow-by-doing-train:<tag>"
export KBD_GPU_TRAIN_IMAGE="<registry>/<namespace>/kubeflow-by-doing-train:<gpu-tag>"
export KBD_SERVE_IMAGE="<registry>/<namespace>/kubeflow-by-doing-serve:<tag>"

# Object storage
export KBD_ARTIFACT_BUCKET="<bucket>"
export KBD_S3_ENDPOINT_URL="<s3-or-compatible-endpoint>"
export AWS_ACCESS_KEY_ID="<access-key-or-service-account-key>"
export AWS_SECRET_ACCESS_KEY="<secret-key>"
export AWS_DEFAULT_REGION="<region>"

# MLflow
export MLFLOW_S3_ENDPOINT_URL="$KBD_S3_ENDPOINT_URL"
export MLFLOW_TRACKING_URI="http://mlflow.kubeflow-by-doing.svc.cluster.local:5000"
export MLFLOW_EXPERIMENT_NAME="kubeflow-by-doing-${KBD_CLOUD_PROVIDER}"

# Runtime
export KBD_ACCELERATOR="cpu"
export KBD_GPU_COUNT="0"
```

## Provider-Neutral Pipeline Parameters

The pipeline should keep accepting:

```text
run_id
cpu_image
gpu_image
accelerator
gpu_count
dataset_uri
image_tag
git_sha
min_accuracy
deploy_after_promotion
```

## Provider-Neutral Secret Keys

Keep a stable application contract:

```yaml
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
KBD_S3_ENDPOINT_URL
KBD_ARTIFACT_BUCKET
MLFLOW_S3_ENDPOINT_URL
MLFLOW_TRACKING_URI
MLFLOW_EXPERIMENT_NAME
```

The names are AWS-shaped because many S3-compatible libraries use them by default. The provider can still be non-AWS.

## Common Anti-Patterns

### Hardcoding provider endpoints in Python

Avoid:

```python
endpoint_url = "https://s3.eu-central-1.amazonaws.com"
```

Prefer:

```python
endpoint_url = os.environ["KBD_S3_ENDPOINT_URL"]
```

### Hardcoding image names in components

Avoid:

```python
image="kubeflow-by-doing/train:local"
```

Prefer:

```python
image=training_image
```

## Acceptance Criteria

You are done when:

- `infra/cloud/README.md` exists
- `infra/cloud/env.example` exists
- provider details are expressed as environment variables
- pipeline parameters remain provider-neutral
- secret key names are stable across providers

## References

- [Kubeflow Pipelines pipeline concept](https://www.kubeflow.org/docs/components/pipelines/concepts/pipeline/)
- [Kubeflow Pipelines components](https://www.kubeflow.org/docs/components/pipelines/concepts/component/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## Next Step

Continue with [Provider Overlays](02-provider-overlays.md).
