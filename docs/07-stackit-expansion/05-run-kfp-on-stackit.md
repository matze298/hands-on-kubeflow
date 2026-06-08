# Run KFP on STACKIT

This page installs or connects Kubeflow Pipelines on SKE and runs the existing pipeline against cloud infrastructure.

## What You Will Build

You will create:

```text
infra/stackit/kfp-install.md
```

You will then run the Chapter 3/4/5 pipeline using:

- SKE as Kubernetes cluster
- registry-hosted images
- STACKIT Object Storage
- Kubernetes Secrets for credentials
- optional MLflow in-cluster tracking

## Why This Matters

This is the actual cloud migration test.

The pipeline should not become a new cloud-specific pipeline. It should be the same workflow with different parameters and secrets.

## Create `infra/stackit/kfp-install.md`

```markdown
# KFP on STACKIT SKE

## Goal

Install standalone Kubeflow Pipelines into the SKE cluster.

## Namespace

KFP system namespace:

```bash
kubectl create namespace kubeflow --dry-run=client -o yaml | kubectl apply -f -
```

Tutorial namespace:

```bash
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
```

## Installation

Use the same pinned KFP version as Chapter 2 unless the SKE cluster requires an update.

```bash
export KFP_VERSION=2.16.1

kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=${KFP_VERSION}"
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=${KFP_VERSION}"
```

## Access

```bash
kubectl -n kubeflow port-forward svc/ml-pipeline-ui 8080:80
kubectl -n kubeflow port-forward svc/ml-pipeline 8888:8888
```
```

## Install KFP

Follow the same KFP install approach used in Chapter 2, with the SKE `KUBECONFIG` active.

```bash
export KUBECONFIG="$PWD/.kube/stackit-kubeconfig.yaml"
kubectl get nodes
```

Then install KFP using the pinned tutorial version and the `env/dev` manifests.

!!! note

    If the KFP manifest paths or version changed, follow the current official KFP installation guide and update this chapter during Codex hardening.

## Apply Secrets

Apply object storage secret:

```bash
kubectl apply -f infra/stackit/object-storage-secret.yaml
```

Apply registry secret if needed:

```bash
kubectl apply -f infra/stackit/container-registry-secret.yaml
```

## Deploy MLflow

Use the Chapter 4 MLflow manifests, but keep in mind:

```text
local tutorial MLflow = simple and disposable
production MLflow     = persistent backend store and hardened auth
```

For the expansion chapter, the simple deployment is acceptable if this is still a disposable tutorial cluster.

```bash
kubectl apply -f infra/mlflow/deployment.yaml
kubectl apply -f infra/mlflow/service.yaml
kubectl -n kubeflow-by-doing rollout status deployment/mlflow --timeout=120s
```

## Compile the Pipeline

```bash
uv run python pipelines/image_classification_pipeline.py
```

## Submit a STACKIT Run

Use the KFP UI or Python submission.

Parameter values:

```text
run_id: stackit-cpu-001
accelerator: cpu
cpu_image: <KBD_TRAIN_IMAGE>
gpu_image: <KBD_TRAIN_IMAGE or GPU image>
min_accuracy: 0.5
dataset_uri: synthetic://tiny-image-classification
git_sha: <git sha>
image_tag: <KBD_TRAIN_IMAGE>
```

## Verify the Run

Inspect:

```bash
kubectl get pods -A --sort-by=.metadata.creationTimestamp
kubectl get events -A --sort-by=.lastTimestamp
```

Check the KFP UI:

```bash
kubectl -n kubeflow port-forward svc/ml-pipeline-ui 8080:80
```

Check object storage:

```bash
source .env.stackit
uv run python scripts/stackit-verify-artifacts.py
```

## Serving on SKE

For the first cloud run, keep serving private:

```bash
kubectl -n kubeflow-by-doing port-forward svc/model-server 8000:8000
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

Do not expose public ingress until the private path works.

## Common Problems

### Pipeline pod cannot pull images

Check image names and pull secrets.

### Pipeline pod cannot access object storage

Check `artifact-store-credentials`.

### Local MinIO endpoint appears in cloud run

Search:

```bash
grep -R "localhost:9000\\|minio.minio" -n manifests pipelines components src || true
```

Cloud runs should use STACKIT object storage endpoint.

### KFP UI works but runs fail immediately

Check KFP pod logs and pipeline step pod logs.

```bash
kubectl get pods -A
kubectl logs -n <namespace> <pod>
```

## Acceptance Criteria

You are done when:

- KFP is reachable on SKE
- object storage secret exists in tutorial namespace
- registry image pull works
- a CPU pipeline run succeeds
- model and metrics artifacts appear in STACKIT Object Storage
- MLflow run appears if tracking is enabled
- serving remains private and testable through port-forwarding

## References

- [Kubeflow Pipelines installation](https://www.kubeflow.org/docs/components/pipelines/operator-guides/installation/)
- [STACKIT Kubernetes Engine documentation](https://docs.stackit.cloud/products/runtime/kubernetes-engine/)
- [STACKIT Object Storage documentation](https://docs.stackit.cloud/products/storage/object-storage/)

## Next Step

Continue with [GPU Node Pool](06-gpu-node-pool.md).
