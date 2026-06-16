# Local Platform Inventory

Use this page when you want to understand what the tutorial creates in the local Kubernetes environment.

The inventory reflects the default local path: `minikube` for the ML/Kubeflow chapters and `kind` as the starter or CPU fallback path. Cloud chapters replace local image loading and local MinIO with provider-specific registry and object-storage services.

## Kubernetes Contexts

| Context | Role | Used in |
|---|---|---|
| `kind-kubeflow-by-doing` | disposable starter cluster and CPU fallback | Chapter 1 starter path |
| `kubeflow-gpu` | default local ML/Kubeflow cluster | Chapters 2 onward |

Check the current context before applying manifests:

```bash
kubectl config current-context
kubectl get nodes -o wide
```

## Namespaces

| Namespace | Purpose | Created in |
|---|---|---|
| `kubeflow-by-doing` | tutorial workloads, training pods, serving, MLflow, app secrets | Chapter 1 |
| `kubeflow` | standalone Kubeflow Pipelines installation | Chapter 2 |
| `minio` | local S3-compatible object storage | Chapter 4 |
| `flyte` | optional Flyte backend | Chapter 12 |
| `kserve` | optional KServe controller and serving platform resources | Chapter 14 |
| `kube-system` | core cluster pods and the NVIDIA device plugin add-on | Chapter 1 GPU path |

Inspect local state:

```bash
kubectl get namespaces
kubectl get pods -n kubeflow-by-doing
kubectl get pods -n kubeflow
kubectl get pods -n minio
```

## Services and Ports

| Service | Namespace | In-cluster port | Local port-forward | Purpose |
|---|---|---:|---:|---|
| `ml-pipeline-ui` | `kubeflow` | `80` | `8080` | Kubeflow Pipelines UI |
| `ml-pipeline` | `kubeflow` | `8888` | `8888` | KFP API endpoint |
| `minio` | `minio` | `9000` | `9000` | S3-compatible object API |
| `minio` | `minio` | `9001` | `9001` | MinIO console |
| `mlflow` | `kubeflow-by-doing` | `5000` | `5000` | MLflow tracking UI/API |
| `model-server` | `kubeflow-by-doing` | `8000` | `8000` | FastAPI model server |
| `flyte-flyte-binary-http` | `flyte` | `8090` | `8090` | optional Flyte API |
| `flyte-flyte-binary-console` | `flyte` | `80` | `8088` | optional Flyte console |
| generated predictor service | `kubeflow-by-doing` | `80` | `8081` or `8082` | optional KServe predictor access |

Common port-forwards:

```bash
kubectl -n kubeflow port-forward svc/ml-pipeline-ui 8080:80
kubectl -n kubeflow port-forward svc/ml-pipeline 8888:8888
kubectl -n minio port-forward svc/minio 9000:9000
kubectl -n minio port-forward svc/minio 9001:9001
kubectl -n kubeflow-by-doing port-forward svc/mlflow 5000:5000
kubectl -n kubeflow-by-doing port-forward svc/model-server 8000:8000
```

## Secrets

| Secret | Namespace | Purpose |
|---|---|---|
| `minio-root-credentials` | `minio` | local MinIO root username and password |
| `artifact-store-credentials` | `kubeflow-by-doing` | S3-compatible credentials for training, serving, MLflow, and pipeline pods |
| provider registry secret | `kubeflow-by-doing` | optional image pull secret in cloud chapters |

The local tutorial credentials are disposable. Do not reuse them in shared or cloud environments.

Verify expected secrets:

```bash
kubectl -n minio get secret minio-root-credentials
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
```

## Images

| Image | Purpose | Local cluster path |
|---|---|---|
| `kubeflow-by-doing/train:local` | CPU training component image | load into `minikube` or `kind` |
| `kubeflow-by-doing/train:gpu-local` | GPU training component image | load into `minikube` |
| `kubeflow-by-doing/serve:local` | FastAPI serving image | load into `minikube` or `kind` |
| `kubeflow-by-doing/flyte-cpu:local` | optional Flyte task image | load into `minikube` |
| `kubeflow-by-doing/kserve:local` | optional KServe custom predictor image | load into `minikube` |

minikube image load examples:

```bash
minikube image load kubeflow-by-doing/train:local -p kubeflow-gpu
minikube image load kubeflow-by-doing/serve:local -p kubeflow-gpu
```

Kind fallback example:

```bash
kind load docker-image kubeflow-by-doing/train:local --name kubeflow-by-doing
```

## Local Files and Generated Artifacts

| Path | Purpose |
|---|---|
| `infra/k8s/` | starter Kubernetes manifests |
| `infra/minio/` | local object-storage manifests |
| `infra/mlflow/` | local MLflow manifests |
| `infra/kserve/` | optional KServe manifests |
| `manifests/model-server/` | local serving manifests |
| `compiled/` | compiled KFP YAML artifacts |
| `outputs/` | local training, evaluation, and smoke-test outputs |
| `build/` | local image tarballs and temporary build products |
| `.flyte/` | machine-local Flyte config, ignored by the repository |

`outputs/`, `build/`, and `.flyte/` are local runtime state. They are useful while following the tutorial, but they are not durable platform storage.

## Default Local Credentials

| System | Local value |
|---|---|
| MinIO root user | `minioadmin` |
| MinIO root password | `minioadmin123` |
| local bucket | `kubeflow-by-doing` |
| local S3 endpoint from host | `http://localhost:9000` |
| local S3 endpoint from cluster | `http://minio.minio.svc.cluster.local:9000` |

These values are intentionally simple for a disposable local tutorial cluster.

## Reset Pointers

Use the FAQ when local state needs cleanup:

- [How to reset minikube](../14-faq/00-overview.md#how-do-i-reset-minikube)
- [How to reset Kubeflow](../14-faq/00-overview.md#how-do-i-reset-kubeflow)

Use the [Verification Matrix](verification-matrix.md) after a reset to decide which checks to rerun.
