# Run the Capstone

This page runs the full capstone locally.

## What You Will Run

You will run:

```text
CPU capstone path
optional GPU capstone path
optional deploy-after-promotion path
```

Start with CPU. Add GPU only after the CPU path succeeds.

## Preflight

Run local checks:

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
uv run mkdocs build --strict
```

## Check Cluster

```bash
kubectl get nodes
kubectl get pods -A
```

Check namespaces:

```bash
kubectl get namespace kubeflow
kubectl get namespace kubeflow-by-doing
```

Check KFP:

```bash
kubectl -n kubeflow get pods
kubectl -n kubeflow get svc
```

Check object storage secret:

```bash
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
```

## Build Images

CPU training image:

```bash
docker build -t kubeflow-by-doing/train:local .
```

Serving image:

```bash
docker build -f Dockerfile.serve -t kubeflow-by-doing/serve:local .
```

Optional GPU image:

```bash
docker build -f Dockerfile.gpu -t kubeflow-by-doing/train:gpu-local .
```

## Make Images Available to the Cluster

### MicroK8s

```bash
docker save kubeflow-by-doing/train:local | sudo microk8s ctr image import -
docker save kubeflow-by-doing/serve:local | sudo microk8s ctr image import -
docker save kubeflow-by-doing/train:gpu-local | sudo microk8s ctr image import -
```

### kind fallback

```bash
kind load docker-image kubeflow-by-doing/train:local --name kubeflow-by-doing
kind load docker-image kubeflow-by-doing/serve:local --name kubeflow-by-doing
kind load docker-image kubeflow-by-doing/train:gpu-local --name kubeflow-by-doing
```

## Ensure Model Server Base Manifests Exist

The deploy step assumes the model server resources exist.

Apply Chapter 5 manifests:

```bash
kubectl apply -f manifests/model-server/configmap.yaml
kubectl apply -f manifests/model-server/deployment.yaml
kubectl apply -f manifests/model-server/service.yaml
kubectl apply -f manifests/model-server/rbac.yaml
```

If the ConfigMap points to an old model, that is fine. The capstone deploy step can update it after promotion.

## Compile the Capstone Pipeline

```bash
uv run python pipelines/capstone_pipeline.py
```

## Open KFP UI

```bash
kubectl -n kubeflow port-forward svc/ml-pipeline-ui 8080:80
```

Open:

```text
http://localhost:8080
```

Upload:

```text
compiled/capstone_pipeline.yaml
```

## Run CPU Capstone

Use parameters:

```text
run_id: capstone-cpu-001
dataset_uri: synthetic://tiny-image-classification
accelerator: cpu
gpu_count: 0
cpu_image: kubeflow-by-doing/train:local
gpu_image: kubeflow-by-doing/train:gpu-local
min_accuracy: 0.5
deploy_after_promotion: false
git_sha: <git rev-parse --short HEAD>
n_train: 256
n_val: 64
image_size: 16
n_classes: 2
epochs: 2
learning_rate: 0.001
batch_size: 32
```

Expected graph:

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
```

Deployment is skipped because:

```text
deploy_after_promotion: false
```

## Run with Deployment Enabled

After CPU run succeeds, run:

```text
run_id: capstone-deploy-001
deploy_after_promotion: true
min_accuracy: 0.5
accelerator: cpu
gpu_count: 0
```

Expected additional steps:

```text
deploy_model
  ↓
smoke_test_model
```

## Optional GPU Capstone

Only run this after Chapter 6 succeeds.

```text
run_id: capstone-gpu-001
accelerator: gpu
gpu_count: 1
gpu_image: kubeflow-by-doing/train:gpu-local
min_accuracy: 0.5
deploy_after_promotion: false
```

## Common Problems

### Pipeline fails before training

Check ingest and validation logs.

### Training fails due to missing secrets

Check:

```bash
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
kubectl describe pod -n <namespace> <training-pod>
```

### Deployment fails

Check RBAC:

```bash
kubectl -n kubeflow-by-doing get serviceaccount pipeline-deployer
kubectl -n kubeflow-by-doing get role model-server-deployer
kubectl -n kubeflow-by-doing get rolebinding model-server-deployer
```

### Smoke test fails

Check the model server:

```bash
kubectl -n kubeflow-by-doing get pods -l app.kubernetes.io/name=model-server
kubectl -n kubeflow-by-doing logs deployment/model-server -c server
```

## Acceptance Criteria

You are done when:

- CPU capstone run succeeds
- promotion path executes when metrics pass
- deployment path can be enabled
- smoke test succeeds when deployment is enabled
- optional GPU capstone either succeeds or is explicitly deferred
- failures can be debugged at KFP and Kubernetes levels

## Next Step

Continue with [Verify End to End](05-verify-end-to-end.md).
