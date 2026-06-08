# Provider Overlays

This page defines provider overlays.

An overlay is a small set of environment values and notes that adapts the tutorial to a provider without changing the pipeline code.

## What You Will Build

You will create:

```text
infra/cloud/provider-matrix.md
infra/cloud/overlays/
├── aws.env.example
├── azure.env.example
├── gcp.env.example
└── generic.env.example
```

## Create the Overlay Folder

```bash
mkdir -p infra/cloud/overlays
```

## Create `provider-matrix.md`

Create `infra/cloud/provider-matrix.md`:

```markdown
# Provider Matrix

| Concern | Portable tutorial interface | Provider-specific implementation |
|---|---|---|
| Kubernetes API | `KUBECONFIG` | EKS, AKS, GKE, SKE, other |
| Training image | `KBD_TRAIN_IMAGE` | ECR, ACR, Artifact Registry, STACKIT CR |
| Serving image | `KBD_SERVE_IMAGE` | ECR, ACR, Artifact Registry, STACKIT CR |
| Object storage endpoint | `KBD_S3_ENDPOINT_URL` | S3 or S3-compatible endpoint |
| Bucket | `KBD_ARTIFACT_BUCKET` | Provider bucket/container |
| Object credentials | `artifact-store-credentials` Secret | IAM key, access key, workload identity |
| MLflow | `MLFLOW_TRACKING_URI` | in-cluster service or managed tracking |
| GPU | `accelerator=gpu`, `gpu_count=1` | GPU node pool and device plugin |
| Cleanup | checklist | provider console/CLI/Terraform |
```

## AWS Overlay

Create `infra/cloud/overlays/aws.env.example`:

```bash
export KBD_CLOUD_PROVIDER="aws"
export KBD_CLUSTER_NAME="kbd-eks"
export KBD_REGION="eu-central-1"
export KUBECONFIG="$PWD/.kube/aws-kubeconfig.yaml"

# ECR image examples
export KBD_REGISTRY="<account-id>.dkr.ecr.${KBD_REGION}.amazonaws.com"
export KBD_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train:aws"
export KBD_GPU_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train:aws-gpu"
export KBD_SERVE_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-serve:aws"

# S3
export KBD_ARTIFACT_BUCKET="<globally-unique-bucket-name>"
export KBD_S3_ENDPOINT_URL="https://s3.${KBD_REGION}.amazonaws.com"
export AWS_DEFAULT_REGION="$KBD_REGION"

# Prefer IAM roles or workload identity where possible.
# Static keys are acceptable only for a disposable tutorial setup.
export AWS_ACCESS_KEY_ID="<access-key-id>"
export AWS_SECRET_ACCESS_KEY="<secret-access-key>"

export MLFLOW_S3_ENDPOINT_URL="$KBD_S3_ENDPOINT_URL"
export MLFLOW_TRACKING_URI="http://mlflow.kubeflow-by-doing.svc.cluster.local:5000"
export MLFLOW_EXPERIMENT_NAME="kubeflow-by-doing-aws"
```

## Azure Overlay

Create `infra/cloud/overlays/azure.env.example`:

```bash
export KBD_CLOUD_PROVIDER="azure"
export KBD_CLUSTER_NAME="kbd-aks"
export KBD_REGION="westeurope"
export KUBECONFIG="$PWD/.kube/azure-kubeconfig.yaml"

# ACR image examples
export KBD_REGISTRY="<registry-name>.azurecr.io"
export KBD_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train:azure"
export KBD_GPU_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train:azure-gpu"
export KBD_SERVE_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-serve:azure"

# Object storage note:
# The tutorial code uses an S3-compatible interface.
# For Azure Blob Storage, use an S3-compatible gateway, adapt storage.py,
# or use a provider-specific object storage abstraction.
export KBD_ARTIFACT_BUCKET="<bucket-or-container-name>"
export KBD_S3_ENDPOINT_URL="<s3-compatible-endpoint-for-azure-or-gateway>"
export AWS_ACCESS_KEY_ID="<access-key-id>"
export AWS_SECRET_ACCESS_KEY="<secret-access-key>"
export AWS_DEFAULT_REGION="$KBD_REGION"

export MLFLOW_S3_ENDPOINT_URL="$KBD_S3_ENDPOINT_URL"
export MLFLOW_TRACKING_URI="http://mlflow.kubeflow-by-doing.svc.cluster.local:5000"
export MLFLOW_EXPERIMENT_NAME="kubeflow-by-doing-azure"
```

## GCP Overlay

Create `infra/cloud/overlays/gcp.env.example`:

```bash
export KBD_CLOUD_PROVIDER="gcp"
export KBD_CLUSTER_NAME="kbd-gke"
export KBD_REGION="europe-west3"
export KUBECONFIG="$PWD/.kube/gcp-kubeconfig.yaml"

# Artifact Registry image examples
export KBD_REGISTRY="${KBD_REGION}-docker.pkg.dev/<project-id>/<repository>"
export KBD_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train:gcp"
export KBD_GPU_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train:gcp-gpu"
export KBD_SERVE_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-serve:gcp"

# KFP supports GCS pipeline roots, but this tutorial's app code uses S3-compatible env vars.
# Use an S3-compatible endpoint/gateway, adapt storage.py, or split app artifacts from KFP pipeline root.
export KBD_ARTIFACT_BUCKET="<bucket-name>"
export KBD_S3_ENDPOINT_URL="<s3-compatible-endpoint-or-gateway>"
export AWS_ACCESS_KEY_ID="<access-key-id>"
export AWS_SECRET_ACCESS_KEY="<secret-access-key>"
export AWS_DEFAULT_REGION="$KBD_REGION"

export MLFLOW_S3_ENDPOINT_URL="$KBD_S3_ENDPOINT_URL"
export MLFLOW_TRACKING_URI="http://mlflow.kubeflow-by-doing.svc.cluster.local:5000"
export MLFLOW_EXPERIMENT_NAME="kubeflow-by-doing-gcp"
```

## Generic Overlay

Create `infra/cloud/overlays/generic.env.example`:

```bash
export KBD_CLOUD_PROVIDER="generic"
export KBD_CLUSTER_NAME="kbd-managed-k8s"
export KBD_REGION="<region>"
export KUBECONFIG="$PWD/.kube/generic-kubeconfig.yaml"

export KBD_REGISTRY="<registry-host>/<namespace>"
export KBD_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train:generic"
export KBD_GPU_TRAIN_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-train:generic-gpu"
export KBD_SERVE_IMAGE="$KBD_REGISTRY/kubeflow-by-doing-serve:generic"

export KBD_ARTIFACT_BUCKET="kubeflow-by-doing"
export KBD_S3_ENDPOINT_URL="<s3-compatible-endpoint>"
export AWS_ACCESS_KEY_ID="<access-key-id>"
export AWS_SECRET_ACCESS_KEY="<secret-access-key>"
export AWS_DEFAULT_REGION="$KBD_REGION"

export MLFLOW_S3_ENDPOINT_URL="$KBD_S3_ENDPOINT_URL"
export MLFLOW_TRACKING_URI="http://mlflow.kubeflow-by-doing.svc.cluster.local:5000"
export MLFLOW_EXPERIMENT_NAME="kubeflow-by-doing-generic"
```

## Copy One Overlay

Example:

```bash
cp infra/cloud/overlays/generic.env.example .env.cloud
# edit .env.cloud
source .env.cloud
```

Do not commit `.env.cloud`.

Add if needed:

```gitignore
.env.cloud
.kube/
```

## Common Problems

### Treating the overlay as infrastructure automation

These files are not Terraform.

They are a minimal explicit configuration layer for the tutorial workflow.

### Mixing providers in one run

Do not use an AWS registry image with a GCP kubeconfig unless that is intentional and pull credentials are configured.

### Assuming all object stores are S3-compatible

Some providers are natively S3-compatible. Others may need a gateway or a small storage abstraction change.

Document the choice in the overlay.

## Acceptance Criteria

You are done when:

- provider matrix exists
- provider overlay examples exist
- one `.env.cloud` exists locally
- `.env.cloud` is ignored by git
- image names and storage endpoints come from the overlay
- pipeline code remains unchanged

## References

- [Amazon EKS documentation](https://docs.aws.amazon.com/eks/)
- [Azure AKS documentation](https://learn.microsoft.com/azure/aks/)
- [Google GKE documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Kubernetes kubeconfig documentation](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)

## Next Step

Continue with [Cloud Secrets and Registries](03-cloud-secrets-and-registries.md).
