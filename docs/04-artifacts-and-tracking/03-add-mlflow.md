# Add Experiment Tracking

This page adds MLflow as a lightweight local experiment tracker.

## What You Will Build

You will create:

```text
infra/mlflow/
├── deployment.yaml
└── service.yaml

src/kubeflow_by_doing/tracking.py
```

You will also update training and evaluation so they can log parameters, metrics, artifacts, and object storage URIs.

## Why This Matters

Object storage keeps files.

Experiment tracking gives those files context:

```text
parameters
metrics
artifacts
tags
run ID
experiment name
```

Kubeflow gives workflow-level visibility. MLflow gives experiment-level visibility familiar to many ML engineers.

This chapter assumes the default `MicroK8s` local Kubernetes path from here on. If you are still on the starter `kind` cluster, switch before continuing so the MLflow service and secret wiring match the rest of the tutorial.

## Add MLflow Dependency

```bash
uv add mlflow boto3
```

## Create the MLflow Deployment

Create `infra/mlflow/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow
  namespace: kubeflow-by-doing
  labels:
    app.kubernetes.io/name: mlflow
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: mlflow
  template:
    metadata:
      labels:
        app.kubernetes.io/name: mlflow
    spec:
      containers:
        - name: mlflow
          image: ghcr.io/mlflow/mlflow:v3.1.1
          command:
            - /bin/sh
            - -c
            - |
              pip install --no-cache-dir boto3 &&
              mlflow server \
                --host 0.0.0.0 \
                --port 5000 \
                --backend-store-uri sqlite:////mlflow/mlflow.db \
                --default-artifact-root s3://kubeflow-by-doing/mlflow-artifacts
          envFrom:
            - secretRef:
                name: artifact-store-credentials
          ports:
            - name: http
              containerPort: 5000
          volumeMounts:
            - name: mlflow-data
              mountPath: /mlflow
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
      volumes:
        - name: mlflow-data
          emptyDir: {}
```

!!! note

    This is a local tutorial deployment. It uses SQLite and `emptyDir` for the backend store, so MLflow metadata is not durable across pod deletion. The artifacts are durable because they go to MinIO. A later production expansion can use Postgres and persistent storage.

Apply:

```bash
mkdir -p infra/mlflow
kubectl apply -f infra/mlflow/deployment.yaml
kubectl -n kubeflow-by-doing rollout status deployment/mlflow --timeout=120s
```

## Create the MLflow Service

Create `infra/mlflow/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mlflow
  namespace: kubeflow-by-doing
  labels:
    app.kubernetes.io/name: mlflow
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: mlflow
  ports:
    - name: http
      port: 5000
      targetPort: http
```

Apply:

```bash
kubectl apply -f infra/mlflow/service.yaml
```

## Access the MLflow UI

Port-forward:

```bash
kubectl -n kubeflow-by-doing port-forward svc/mlflow 5000:5000
```

Open:

```text
http://localhost:5000
```

Inside Kubernetes, the tracking URI is:

```text
http://mlflow.kubeflow-by-doing.svc.cluster.local:5000
```

## Add MLflow Environment Variables to the Secret

Update `infra/minio/app-secret.yaml` to include:

```yaml
  MLFLOW_TRACKING_URI: http://mlflow.kubeflow-by-doing.svc.cluster.local:5000
  MLFLOW_EXPERIMENT_NAME: kubeflow-by-doing
```

Apply again:

```bash
kubectl apply -f infra/minio/app-secret.yaml
```

For local shell testing:

```bash
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=kubeflow-by-doing
```

## Add `tracking.py`

Create `src/kubeflow_by_doing/tracking.py`:

```python
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

import mlflow


def configure_mlflow() -> str:
    """Configure MLflow from environment variables and return the experiment name."""
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME", "kubeflow-by-doing")

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    mlflow.set_experiment(experiment_name)
    return experiment_name


@contextmanager
def mlflow_run(
    *,
    run_name: str,
    tags: dict[str, str] | None = None,
) -> Iterator[str]:
    """Start an MLflow run and yield its run ID."""
    configure_mlflow()

    with mlflow.start_run(run_name=run_name) as active_run:
        if tags:
            mlflow.set_tags(tags)
        yield active_run.info.run_id


def log_params(params: dict[str, str | int | float | bool]) -> None:
    mlflow.log_params(params)


def log_metrics(metrics: dict[str, int | float]) -> None:
    mlflow.log_metrics(metrics)


def log_artifact_path(path: str) -> None:
    mlflow.log_artifact(path)
```

## Update Training to Log to MLflow

Modify `train` in `src/kubeflow_by_doing/train.py`.

Add optional arguments:

```python
tracking: bool = False
kfp_run_id: str | None = None
image_tag: str | None = None
git_sha: str | None = None
```

After `summary` and artifact files are created, add:

```python
if tracking:
    from kubeflow_by_doing.tracking import log_artifact_path, log_params, mlflow_run

    tags = {"stage": "train"}
    if kfp_run_id:
        tags["kfp_run_id"] = kfp_run_id
    if image_tag:
        tags["image_tag"] = image_tag
    if git_sha:
        tags["git_sha"] = git_sha

    with mlflow_run(run_name=f"train-{run_id or 'local'}", tags=tags) as mlflow_run_id:
        log_params(
            {
                "epochs": epochs,
                "learning_rate": learning_rate,
                "seed": seed,
                "n_train": n_train,
                "n_val": n_val,
                "batch_size": batch_size,
                "device": str(torch_device),
            }
        )
        log_artifact_path(str(model_path))
        log_artifact_path(str(summary_path))
        summary["mlflow_run_id"] = mlflow_run_id
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
```

## Update Evaluation to Log to MLflow

Modify `evaluate` in `src/kubeflow_by_doing/evaluate.py`.

Add optional arguments:

```python
tracking: bool = False
kfp_run_id: str | None = None
image_tag: str | None = None
git_sha: str | None = None
```

After metrics are computed and written:

```python
if tracking:
    from kubeflow_by_doing.tracking import log_artifact_path, log_metrics, mlflow_run

    tags = {"stage": "evaluate"}
    if kfp_run_id:
        tags["kfp_run_id"] = kfp_run_id
    if image_tag:
        tags["image_tag"] = image_tag
    if git_sha:
        tags["git_sha"] = git_sha

    numeric_metrics = {
        key: value
        for key, value in metrics.items()
        if isinstance(value, int | float)
    }

    with mlflow_run(run_name=f"evaluate-{run_id or 'local'}", tags=tags) as mlflow_run_id:
        log_metrics(numeric_metrics)
        log_artifact_path(str(metrics_path))
        metrics["mlflow_run_id"] = mlflow_run_id
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
```

## Update the CLI

Add options to both `train_model` and `evaluate_model`:

```python
tracking: bool = typer.Option(False, help="Log run information to MLflow."),
kfp_run_id: str | None = typer.Option(None, help="Kubeflow Pipelines run ID."),
image_tag: str | None = typer.Option(None, help="Container image tag."),
git_sha: str | None = typer.Option(None, help="Git commit SHA."),
```

Pass them into `train` and `evaluate`.

## Test MLflow Locally

Make sure port forwarding is running:

```bash
kubectl -n kubeflow-by-doing port-forward svc/mlflow 5000:5000
kubectl -n minio port-forward svc/minio 9000:9000
```

Set environment variables:

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export AWS_DEFAULT_REGION=us-east-1
export KBD_S3_ENDPOINT_URL=http://localhost:9000
export KBD_ARTIFACT_BUCKET=kubeflow-by-doing
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=kubeflow-by-doing
```

Train:

```bash
mkdir -p outputs/mlflow-train

uv run kbd train-model \
  --output-dir outputs/mlflow-train \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --device cpu \
  --run-id manual-mlflow-001 \
  --upload-artifacts \
  --tracking \
  --image-tag kubeflow-by-doing/train:local \
  --git-sha "$(git rev-parse --short HEAD)"
```

Evaluate:

```bash
uv run kbd evaluate-model \
  --model-dir outputs/mlflow-train \
  --metrics-path outputs/mlflow-train/metrics.json \
  --seed 42 \
  --device cpu \
  --run-id manual-mlflow-001 \
  --upload-artifacts \
  --tracking \
  --image-tag kubeflow-by-doing/train:local \
  --git-sha "$(git rev-parse --short HEAD)"
```

Open:

```text
http://localhost:5000
```

Verify that runs appear.

## Common Problems

### MLflow UI opens but artifacts do not upload

Check:

```bash
env | grep MLFLOW_S3_ENDPOINT_URL
env | grep AWS_
```

MLflow needs S3 credentials and endpoint information.

### MLflow pod crashes

Inspect logs:

```bash
kubectl -n kubeflow-by-doing logs deployment/mlflow
```

### Runs log locally instead of to the tracking server

Check:

```bash
echo "$MLFLOW_TRACKING_URI"
```

## Cleanup

```bash
kubectl delete -f infra/mlflow/service.yaml --ignore-not-found
kubectl delete -f infra/mlflow/deployment.yaml --ignore-not-found
```

This removes local MLflow metadata stored in the pod volume.

Artifacts stored in MinIO remain unless MinIO is deleted.

## Acceptance Criteria

You are done when:

- MLflow runs in Kubernetes
- the UI opens at `http://localhost:5000`
- local training logs an MLflow run
- local evaluation logs an MLflow run
- parameters and metrics are visible in MLflow
- artifacts are uploaded to MinIO-backed storage
- MLflow run IDs are written into local summary or metrics files

## References

- [MLflow tracking docs](https://mlflow.org/docs/latest/tracking.html)
- [MLflow artifact store docs](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/)
- [MLflow tracking server docs](https://mlflow.org/docs/latest/tracking/server/)

## Next Step

Continue with [Trace Lineage](04-trace-lineage.md).
