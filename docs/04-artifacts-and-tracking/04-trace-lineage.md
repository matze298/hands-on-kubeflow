# Trace Lineage

This page adds an explicit lineage record to the workflow.

## What You Will Build

You will create:

```text
src/kubeflow_by_doing/lineage.py
components/write_lineage.py
```

Then you will update the pipeline so each run records:

- Git SHA
- image tag
- dataset URI
- model URI
- metrics URI
- KFP run ID
- MLflow run information where available
- artifact prefix

## Why This Matters

A model without lineage is difficult to trust.

A useful platform should answer:

```text
What code produced this model?
Which image ran?
Which dataset was used?
Where are the metrics?
Which KFP run created it?
Which MLflow run tracked it?
Can I find the exact artifacts?
```

KFP provides pipeline metadata. MLflow provides experiment metadata. The lineage record ties the pieces together in a simple portable JSON file.

## Add `lineage.py`

Create `src/kubeflow_by_doing/lineage.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class LineageRecord:
    run_id: str
    git_sha: str
    image_tag: str
    dataset_uri: str
    model_uri: str
    metrics_uri: str
    kfp_run_id: str | None
    mlflow_train_run_id: str | None
    mlflow_eval_run_id: str | None
    artifact_prefix: str


def write_lineage_record(
    *,
    record: LineageRecord,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(record), indent=2, sort_keys=True),
        encoding="utf-8",
    )
```

## Add a Lineage Component

Create `components/write_lineage.py`:

```python
from __future__ import annotations

from kfp import dsl
from kfp.dsl import Artifact, Output


@dsl.component(
    base_image="python:3.12-slim",
    packages_to_install=["boto3"],
)
def write_lineage(
    lineage: Output[Artifact],
    run_id: str,
    git_sha: str,
    image_tag: str,
    dataset_uri: str,
    model_uri: str,
    metrics_uri: str,
    artifact_prefix: str,
    kfp_run_id: str = "",
    mlflow_train_run_id: str = "",
    mlflow_eval_run_id: str = "",
) -> None:
    from dataclasses import asdict, dataclass
    from pathlib import Path
    import json
    import os

    import boto3
    from botocore.client import Config

    @dataclass(frozen=True)
    class LineageRecord:
        run_id: str
        git_sha: str
        image_tag: str
        dataset_uri: str
        model_uri: str
        metrics_uri: str
        kfp_run_id: str | None
        mlflow_train_run_id: str | None
        mlflow_eval_run_id: str | None
        artifact_prefix: str

    record = LineageRecord(
        run_id=run_id,
        git_sha=git_sha,
        image_tag=image_tag,
        dataset_uri=dataset_uri,
        model_uri=model_uri,
        metrics_uri=metrics_uri,
        kfp_run_id=kfp_run_id or None,
        mlflow_train_run_id=mlflow_train_run_id or None,
        mlflow_eval_run_id=mlflow_eval_run_id or None,
        artifact_prefix=artifact_prefix,
    )

    output_path = Path(lineage.path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(record), indent=2, sort_keys=True),
        encoding="utf-8",
    )

    endpoint_url = os.environ["KBD_S3_ENDPOINT_URL"]
    bucket = os.environ["KBD_ARTIFACT_BUCKET"]
    key = f"runs/{run_id}/lineage/lineage.json"

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        config=Config(signature_version="s3v4"),
    )
    client.upload_file(str(output_path), bucket, key)
```

!!! note

    This component duplicates a small amount of logic instead of importing the project package. That keeps the first version simple. Codex can later convert it to a containerized component using the project image.

## Update Components to Use Secrets

The training, evaluation, and lineage components need environment variables from `artifact-store-credentials`.

Depending on the KFP SDK version, add Kubernetes-specific configuration in the pipeline after creating tasks.

Target intent:

```python
from kfp import kubernetes

kubernetes.use_secret_as_env(
    task,
    secret_name="artifact-store-credentials",
    secret_key_to_env={
        "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION": "AWS_DEFAULT_REGION",
        "KBD_S3_ENDPOINT_URL": "KBD_S3_ENDPOINT_URL",
        "KBD_ARTIFACT_BUCKET": "KBD_ARTIFACT_BUCKET",
        "MLFLOW_S3_ENDPOINT_URL": "MLFLOW_S3_ENDPOINT_URL",
        "MLFLOW_TRACKING_URI": "MLFLOW_TRACKING_URI",
        "MLFLOW_EXPERIMENT_NAME": "MLFLOW_EXPERIMENT_NAME",
    },
)
```

If your installed KFP version uses a different helper, adapt this during Codex hardening.

## Update the Pipeline

Update `pipelines/image_classification_pipeline.py`.

Target pipeline parameters:

```python
run_id: str = "manual-kfp-001"
git_sha: str = "unknown"
image_tag: str = "kubeflow-by-doing/train:local"
dataset_uri: str = "synthetic://tiny-image-classification"
min_accuracy: float = 0.8
```

Target flow:

```text
train_model
  ↓
evaluate_model
  ↓
read_accuracy
  ↓
if accuracy >= min_accuracy:
      promote_model
      write_lineage
```

Add the lineage component after promotion:

```python
from components.write_lineage import write_lineage
```

Create derived URIs:

```python
artifact_prefix = f"s3://kubeflow-by-doing/runs/{run_id}"
model_uri = f"{artifact_prefix}/models/model.pt"
metrics_uri = f"{artifact_prefix}/metrics/metrics.json"
```

Pass these values to `write_lineage`.

## Update Container Component Arguments

Training should receive:

```text
--run-id
--upload-artifacts
--tracking
--image-tag
--git-sha
```

Evaluation should receive the same lineage-related arguments.

Target CLI arguments in the KFP component:

```python
"--run-id",
run_id,
"--upload-artifacts",
"--tracking",
"--image-tag",
image_tag,
"--git-sha",
git_sha,
```

## Rebuild and Reload the Image

Because the Python package changed:

```bash
uv sync
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
mkdir -p build
docker build -t kubeflow-by-doing/train:local .
docker save kubeflow-by-doing/train:local > build/train-image.tar
sudo microk8s ctr image import build/train-image.tar
```

If you are using the `kind` fallback path, load the image with:

```bash
kind load docker-image kubeflow-by-doing/train:local --name kubeflow-by-doing
```

## Compile the Pipeline

```bash
uv run python pipelines/image_classification_pipeline.py
```

Verify:

```bash
ls -lh compiled/image_classification_pipeline.yaml
```

## Run the Pipeline

Open KFP:

```bash
kubectl -n kubeflow port-forward svc/ml-pipeline-ui 8080:80
```

Open:

```text
http://localhost:8080
```

Run with:

```text
run_id: manual-kfp-001
git_sha: <output of git rev-parse --short HEAD>
image_tag: kubeflow-by-doing/train:local
dataset_uri: synthetic://tiny-image-classification
min_accuracy: 0.5
```

## Verify MinIO Artifacts

With MinIO port-forwarding active:

```bash
uv run python - <<'PY'
from kubeflow_by_doing.storage import ObjectStorageConfig, s3_client

config = ObjectStorageConfig.from_env()
client = s3_client(config)

response = client.list_objects_v2(
    Bucket=config.bucket,
    Prefix="runs/manual-kfp-001/",
)

for item in response.get("Contents", []):
    print(f"s3://{config.bucket}/{item['Key']}")
PY
```

Expected shape:

```text
s3://kubeflow-by-doing/runs/manual-kfp-001/models/model.pt
s3://kubeflow-by-doing/runs/manual-kfp-001/models/train_summary.json
s3://kubeflow-by-doing/runs/manual-kfp-001/metrics/metrics.json
s3://kubeflow-by-doing/runs/manual-kfp-001/lineage/lineage.json
```

## Verify MLflow

Open:

```text
http://localhost:5000
```

Check:

- training run
- evaluation run
- parameters
- metrics
- tags such as `git_sha`, `image_tag`, and `kfp_run_id` if available

## Verify Lineage JSON

Expected shape:

```json
{
  "artifact_prefix": "s3://kubeflow-by-doing/runs/manual-kfp-001",
  "dataset_uri": "synthetic://tiny-image-classification",
  "git_sha": "abc1234",
  "image_tag": "kubeflow-by-doing/train:local",
  "kfp_run_id": "manual-kfp-001",
  "metrics_uri": "s3://kubeflow-by-doing/runs/manual-kfp-001/metrics/metrics.json",
  "mlflow_eval_run_id": null,
  "mlflow_train_run_id": null,
  "model_uri": "s3://kubeflow-by-doing/runs/manual-kfp-001/models/model.pt",
  "run_id": "manual-kfp-001"
}
```

## Common Problems

### KFP run ID is hard to access inside a component

For the first version, pass a tutorial `run_id` pipeline parameter.

Later, Codex can integrate actual KFP run metadata if the local KFP setup exposes it cleanly.

### MLflow run IDs are not connected to lineage

The simple CLI logging writes MLflow run IDs into summary and metrics files. Passing those values as KFP outputs requires additional parsing components.

For the first version, treat MLflow run IDs as optional lineage data. Keep them `null` when the step cannot surface them yet, and refine the lineage component later if you want to wire them through explicitly.

### Secret environment variables are missing in KFP pods

Inspect the pod:

```bash
kubectl describe pod -n <namespace> <pod-name>
```

Look for environment variables from `artifact-store-credentials`.

## Acceptance Criteria

You are done when:

- `lineage.py` exists
- `write_lineage` component exists
- KFP tasks receive object storage and MLflow environment variables
- the pipeline uploads model and metrics artifacts
- the pipeline writes a lineage record
- lineage JSON includes Git SHA, image tag, dataset URI, model URI, metrics URI, KFP run ID, and MLflow run information where available
- MinIO contains the expected `runs/<run_id>/...` object tree
- MLflow contains training and evaluation runs

## References

- [Kubeflow Pipelines artifacts](https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/artifacts/)
- [Kubeflow Pipelines metadata](https://www.kubeflow.org/docs/components/pipelines/concepts/metadata/)
- [MLflow tracking](https://mlflow.org/docs/latest/tracking.html)
- [MLflow artifact stores](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/)

## Next Step

Continue with Chapter 5: Local Serving.
