# Define Artifact Layout

This page defines a portable artifact layout and adds Python helpers for object storage.

## What You Will Build

You will create:

```text
src/kubeflow_by_doing/storage.py
```

You will also update the training and evaluation commands so they can upload artifacts to MinIO.

## Why This Matters

Artifact paths should not be accidental.

A consistent layout makes it easier to inspect runs, move from local MinIO to cloud object storage, and connect training outputs to serving or model registry steps later.

## Target Layout

```text
s3://kubeflow-by-doing/
├── datasets/
├── models/
├── metrics/
├── reports/
├── predictions/
└── lineage/
```

For each pipeline run, use a run-scoped prefix:

```text
s3://kubeflow-by-doing/runs/<run_id>/
├── datasets/
├── models/
├── metrics/
├── reports/
├── predictions/
└── lineage/
```

## Add `storage.py`

Create `src/kubeflow_by_doing/storage.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import boto3
from botocore.client import Config


@dataclass(frozen=True)
class ObjectStorageConfig:
    """Configuration for S3-compatible object storage."""

    endpoint_url: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    region_name: str = "us-east-1"

    @classmethod
    def from_env(cls) -> "ObjectStorageConfig":
        return cls(
            endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
            bucket=os.environ["KBD_ARTIFACT_BUCKET"],
            access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        )


def s3_client(config: ObjectStorageConfig):
    """Create a boto3 S3 client for AWS or S3-compatible object storage."""
    return boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        region_name=config.region_name,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket(config: ObjectStorageConfig) -> None:
    client = s3_client(config)
    existing = [bucket["Name"] for bucket in client.list_buckets()["Buckets"]]
    if config.bucket not in existing:
        client.create_bucket(Bucket=config.bucket)


def upload_file(
    *,
    local_path: Path,
    key: str,
    config: ObjectStorageConfig,
) -> str:
    """Upload a file and return its s3:// URI."""
    client = s3_client(config)
    client.upload_file(str(local_path), config.bucket, key)
    return f"s3://{config.bucket}/{key}"


def upload_directory(
    *,
    local_dir: Path,
    prefix: str,
    config: ObjectStorageConfig,
) -> list[str]:
    """Upload all files from a directory and return their s3:// URIs."""
    uris: list[str] = []
    for path in local_dir.rglob("*"):
        if path.is_file():
            relative = path.relative_to(local_dir).as_posix()
            key = f"{prefix.rstrip('/')}/{relative}"
            uris.append(upload_file(local_path=path, key=key, config=config))
    return uris


def run_prefix(run_id: str) -> str:
    return f"runs/{run_id}"
```

## Update Dependencies

Add `boto3` if you have not already done so:

```bash
uv add boto3
```

## Add Local Environment Variables

For local shell testing with port-forwarding:

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export AWS_DEFAULT_REGION=us-east-1
export KBD_S3_ENDPOINT_URL=http://localhost:9000
export KBD_ARTIFACT_BUCKET=kubeflow-by-doing
export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
```

For Kubernetes pods, these values come from the `artifact-store-credentials` Secret.

## Test Uploading a File

Make sure MinIO API port forwarding is running:

```bash
kubectl -n minio port-forward svc/minio 9000:9000
```

Create a small local artifact:

```bash
mkdir -p outputs/artifact-test
echo "hello artifacts" > outputs/artifact-test/hello.txt
```

Upload it:

```bash
uv run python - <<'PY'
from pathlib import Path

from kubeflow_by_doing.storage import ObjectStorageConfig, ensure_bucket, upload_file

config = ObjectStorageConfig.from_env()
ensure_bucket(config)

uri = upload_file(
    local_path=Path("outputs/artifact-test/hello.txt"),
    key="reports/hello.txt",
    config=config,
)

print(uri)
PY
```

Expected:

```text
s3://kubeflow-by-doing/reports/hello.txt
```

## Update `train.py` to Upload Model Artifacts

Modify `src/kubeflow_by_doing/train.py`.

Add optional arguments to `train`:

```python
run_id: str | None = None
upload_artifacts: bool = False
```

After writing `model.pt` and `train_summary.json`, add:

```python
if upload_artifacts:
    if run_id is None:
        raise ValueError("run_id is required when upload_artifacts=True")

    from kubeflow_by_doing.storage import (
        ObjectStorageConfig,
        ensure_bucket,
        run_prefix,
        upload_directory,
    )

    storage_config = ObjectStorageConfig.from_env()
    ensure_bucket(storage_config)

    prefix = f"{run_prefix(run_id)}/models"
    uploaded_uris = upload_directory(
        local_dir=output_dir,
        prefix=prefix,
        config=storage_config,
    )
    summary["model_artifact_prefix"] = f"s3://{storage_config.bucket}/{prefix}"
    summary["uploaded_artifacts"] = uploaded_uris

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
```

## Update `evaluate.py` to Upload Metrics

Modify `src/kubeflow_by_doing/evaluate.py`.

Add optional arguments to `evaluate`:

```python
run_id: str | None = None
upload_artifacts: bool = False
```

After writing `metrics_path`, add:

```python
if upload_artifacts:
    if run_id is None:
        raise ValueError("run_id is required when upload_artifacts=True")

    from kubeflow_by_doing.storage import (
        ObjectStorageConfig,
        ensure_bucket,
        run_prefix,
        upload_file,
    )

    storage_config = ObjectStorageConfig.from_env()
    ensure_bucket(storage_config)

    key = f"{run_prefix(run_id)}/metrics/{metrics_path.name}"
    metrics_uri = upload_file(
        local_path=metrics_path,
        key=key,
        config=storage_config,
    )
    metrics["metrics_uri"] = metrics_uri

    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
```

## Update `cli.py`

Add options to `train_model`:

```python
run_id: str | None = typer.Option(None, help="Run ID used for artifact layout."),
upload_artifacts: bool = typer.Option(False, help="Upload artifacts to object storage."),
```

Pass them into `train`:

```python
run_id=run_id,
upload_artifacts=upload_artifacts,
```

Add the same options to `evaluate_model` and pass them into `evaluate`.

## Local Training with Artifact Upload

Run:

```bash
mkdir -p outputs/artifact-train

uv run kbd train-model \
  --output-dir outputs/artifact-train \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --device cpu \
  --run-id manual-local-001 \
  --upload-artifacts
```

Then evaluate:

```bash
uv run kbd evaluate-model \
  --model-dir outputs/artifact-train \
  --metrics-path outputs/artifact-train/metrics.json \
  --seed 42 \
  --device cpu \
  --run-id manual-local-001 \
  --upload-artifacts
```

## Verify in MinIO

```bash
uv run python - <<'PY'
from kubeflow_by_doing.storage import ObjectStorageConfig, s3_client

config = ObjectStorageConfig.from_env()
client = s3_client(config)

response = client.list_objects_v2(
    Bucket=config.bucket,
    Prefix="runs/manual-local-001/",
)

for item in response.get("Contents", []):
    print(f"s3://{config.bucket}/{item['Key']}")
PY
```

Expected shape:

```text
s3://kubeflow-by-doing/runs/manual-local-001/models/model.pt
s3://kubeflow-by-doing/runs/manual-local-001/models/train_summary.json
s3://kubeflow-by-doing/runs/manual-local-001/metrics/metrics.json
```

## Common Problems

### Environment variables are missing

Check:

```bash
env | grep -E "KBD_|AWS_|MLFLOW_"
```

### Upload works locally but not in Kubernetes

Local shell uses:

```text
http://localhost:9000
```

Kubernetes pods must use:

```text
http://minio.minio.svc.cluster.local:9000
```

### `NoCredentialsError`

The pod probably does not have the `artifact-store-credentials` Secret attached as environment variables.

## Acceptance Criteria

You are done when:

- `storage.py` exists
- local upload to MinIO works
- the artifact layout uses `runs/<run_id>/...`
- training can upload model artifacts
- evaluation can upload metrics
- uploaded files are visible in MinIO

## References

- [boto3 S3 client documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [MinIO Python SDK](https://minio-py.min.io/)
- [Kubeflow Pipelines artifacts](https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/artifacts/)

## Next Step

Continue with [Add Experiment Tracking](03-add-mlflow.md).
