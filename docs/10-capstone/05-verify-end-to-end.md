# Verify End to End

This page verifies the capstone outputs.

## What You Will Verify

You will verify:

- KFP run status
- object storage artifacts
- lineage
- registry record
- MLflow tracking
- served endpoint
- smoke test result

## KFP Run Status

In the KFP UI, confirm:

```text
run status: succeeded
```

Then inspect each step:

```text
ingest_data
validate_data
train_model
evaluate_model
record_or_register_model
deploy_model
smoke_test_endpoint
```

## Verify Object Storage

Set local env for MinIO:

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export AWS_DEFAULT_REGION=us-east-1
export KBD_S3_ENDPOINT_URL=http://localhost:9000
export KBD_ARTIFACT_BUCKET=kubeflow-by-doing
```

Port-forward MinIO if needed:

```bash
kubectl -n minio port-forward svc/minio 9000:9000
```

List run artifacts:

```bash
uv run python - <<'PY'
import os
import boto3
from botocore.client import Config

run_id = "capstone-deploy-001"
bucket = os.environ["KBD_ARTIFACT_BUCKET"]

client = boto3.client(
    "s3",
    endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    config=Config(signature_version="s3v4"),
)

response = client.list_objects_v2(Bucket=bucket, Prefix=f"runs/{run_id}/")

for item in response.get("Contents", []):
    print(f"s3://{bucket}/{item['Key']}")
PY
```

Expected shape:

```text
s3://kubeflow-by-doing/runs/capstone-deploy-001/datasets/dataset_manifest.json
s3://kubeflow-by-doing/runs/capstone-deploy-001/validation/validation_report.json
s3://kubeflow-by-doing/runs/capstone-deploy-001/models/model.pt
s3://kubeflow-by-doing/runs/capstone-deploy-001/models/train_summary.json
s3://kubeflow-by-doing/runs/capstone-deploy-001/metrics/metrics.json
s3://kubeflow-by-doing/runs/capstone-deploy-001/lineage/lineage.json
s3://kubeflow-by-doing/runs/capstone-deploy-001/registry/model_record.json
```

## Download and Inspect Lineage

```bash
uv run python - <<'PY'
import os
import json
import boto3
from botocore.client import Config

run_id = "capstone-deploy-001"
bucket = os.environ["KBD_ARTIFACT_BUCKET"]
key = f"runs/{run_id}/lineage/lineage.json"

client = boto3.client(
    "s3",
    endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    config=Config(signature_version="s3v4"),
)

body = client.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
print(json.dumps(json.loads(body), indent=2))
PY
```

Check for:

```text
run_id
git_sha
image_tag
dataset_uri
model_uri
metrics_uri
artifact_prefix
```

## Verify Registry Record

```bash
uv run python - <<'PY'
import os
import json
import boto3
from botocore.client import Config

run_id = "capstone-deploy-001"
bucket = os.environ["KBD_ARTIFACT_BUCKET"]
key = f"runs/{run_id}/registry/model_record.json"

client = boto3.client(
    "s3",
    endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    config=Config(signature_version="s3v4"),
)

body = client.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")
print(json.dumps(json.loads(body), indent=2))
PY
```

Check:

```text
promoted: true
```

## Verify MLflow

Port-forward:

```bash
kubectl -n kubeflow-by-doing port-forward svc/mlflow 5000:5000
```

Open:

```text
http://localhost:5000
```

Check:

- training run
- evaluation run
- parameters
- metrics
- tags
- artifacts

## Verify Served Endpoint

Port-forward:

```bash
kubectl -n kubeflow-by-doing port-forward svc/model-server 8000:8000
```

Health:

```bash
curl http://localhost:8000/healthz
```

Prediction:

```bash
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

## Create `src/kubeflow_by_doing/capstone_report.py`

Create a small local reporting helper:

```python
from __future__ import annotations

import json
import os

import boto3
from botocore.client import Config


def main() -> None:
    run_id = os.environ["KBD_RUN_ID"]
    bucket = os.environ["KBD_ARTIFACT_BUCKET"]

    client = boto3.client(
        "s3",
        endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        config=Config(signature_version="s3v4"),
    )

    response = client.list_objects_v2(Bucket=bucket, Prefix=f"runs/{run_id}/")
    objects = [f"s3://{bucket}/{item['Key']}" for item in response.get("Contents", [])]

    print(json.dumps({"run_id": run_id, "objects": objects}, indent=2))


if __name__ == "__main__":
    main()
```

Run:

```bash
export KBD_RUN_ID=capstone-deploy-001
uv run python -m kubeflow_by_doing.capstone_report
```

## Common Problems

### Expected artifact missing

Check the corresponding pipeline step logs.

Examples:

```text
missing dataset manifest → ingest_data
missing validation report → validate_data
missing model → train_model
missing metrics → evaluate_model
missing registry record → record_or_register_model
missing lineage → write_lineage
```

### Served endpoint returns old model

Check `model-server-config`:

```bash
kubectl -n kubeflow-by-doing get configmap model-server-config -o yaml
```

Check pod restart time:

```bash
kubectl -n kubeflow-by-doing get pods -l app.kubernetes.io/name=model-server
```

### MLflow missing but artifacts exist

MLflow is tracking metadata. Object storage is the durable artifact source.

Check MLflow env vars and service availability.

## Acceptance Criteria

You are done when:

- KFP run succeeded
- expected object storage keys exist
- lineage JSON can be inspected
- registry record says promoted
- MLflow run exists if tracking is enabled
- model server responds to health
- model server returns predictions
- capstone report script lists artifacts

## Next Step

Continue with [Cloud Mapping](06-cloud-mapping.md).
