# Object Storage Abstraction

This page keeps artifacts portable across cloud providers.

## What You Will Build

You will create:

```text
infra/cloud/checks/object-storage-check.py
infra/cloud/checks/object-storage-pod-check.yaml
```

You will also define how KFP pipeline roots and application artifact storage should relate.

## Two Artifact Layers

There are two related but separate artifact layers:

```text
KFP pipeline artifacts
application artifacts
```

### KFP Pipeline Artifacts

KFP stores pipeline artifacts under a pipeline root.

Conceptually:

```text
pipeline_root = s3://<bucket>/kfp/
```

or:

```text
pipeline_root = gs://<bucket>/kfp/
```

depending on backend support.

### Application Artifacts

The tutorial code writes artifacts under:

```text
s3://<bucket>/runs/<run_id>/
```

Examples:

```text
s3://kubeflow-by-doing/runs/cloud-001/models/model.pt
s3://kubeflow-by-doing/runs/cloud-001/metrics/metrics.json
s3://kubeflow-by-doing/runs/cloud-001/lineage/lineage.json
```

## Recommended Pattern

Use the same bucket but separate prefixes:

```text
s3://<bucket>/
├── kfp/
└── runs/
```

This keeps KFP internals and tutorial application artifacts separate.

## Create Object Storage Check

Create `infra/cloud/checks/object-storage-check.py`:

```python
from __future__ import annotations

import os
from pathlib import Path

import boto3
from botocore.client import Config


def main() -> None:
    endpoint_url = os.environ["KBD_S3_ENDPOINT_URL"]
    bucket = os.environ["KBD_ARTIFACT_BUCKET"]

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_DEFAULT_REGION"),
        config=Config(signature_version="s3v4"),
    )

    path = Path("outputs/cloud-object-storage-check.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("cloud object storage check\n", encoding="utf-8")

    key = "reports/cloud-object-storage-check.txt"
    client.upload_file(str(path), bucket, key)

    response = client.list_objects_v2(Bucket=bucket, Prefix="reports/")
    for item in response.get("Contents", []):
        print(f"s3://{bucket}/{item['Key']}")


if __name__ == "__main__":
    main()
```

Run:

```bash
source .env.cloud
uv add boto3
uv run python infra/cloud/checks/object-storage-check.py
```

## Kubernetes Object Storage Check

Create `infra/cloud/checks/object-storage-pod-check.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: object-storage-pod-check
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  containers:
    - name: check
      image: python:3.12-slim
      command:
        - /bin/sh
        - -c
        - |
          pip install --no-cache-dir boto3 &&
          python - <<'PY'
          import os
          import boto3
          from botocore.client import Config

          client = boto3.client(
              "s3",
              endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
              aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
              aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
              region_name=os.environ.get("AWS_DEFAULT_REGION"),
              config=Config(signature_version="s3v4"),
          )

          bucket = os.environ["KBD_ARTIFACT_BUCKET"]
          response = client.list_objects_v2(Bucket=bucket, Prefix="reports/")
          print(response.get("Contents", []))
          PY
      envFrom:
        - secretRef:
            name: artifact-store-credentials
```

Apply:

```bash
kubectl apply -f infra/cloud/checks/object-storage-pod-check.yaml
kubectl -n kubeflow-by-doing logs pod/object-storage-pod-check
kubectl -n kubeflow-by-doing delete pod object-storage-pod-check --ignore-not-found
```

## KFP Pipeline Root

KFP can use object storage as the pipeline root. Keep this configurable.

Target parameter or config:

```text
pipeline_root=s3://<bucket>/kfp/
```

or provider-native equivalent if KFP supports it directly.

When compiling or submitting a pipeline, prefer making the pipeline root explicit.

Conceptual example:

```python
@dsl.pipeline(
    name="image-classification-cloud",
    pipeline_root="s3://kubeflow-by-doing/kfp/",
)
def image_classification_pipeline(...):
    ...
```

For provider overlays, Codex can make `pipeline_root` configurable at compile or submission time.

## S3-Compatible vs Provider-Native Storage

### S3-Compatible Path

Best when:

- provider supports S3 API
- MLflow artifacts use S3
- application code already uses boto3
- you want one storage implementation

### Provider-Native Path

Best when:

- provider has strong native integration
- KFP supports the provider storage directly
- you want workload identity instead of static keys
- you are willing to add a storage adapter

For this tutorial, prefer the S3-compatible path unless the provider makes that awkward.

## Common Problems

### KFP artifacts work but app artifacts fail

KFP pipeline root and app artifact storage may use different credentials or mechanisms.

Check both separately.

### App artifacts work but KFP artifacts fail

Check KFP pipeline root configuration and KFP object store credentials.

### Provider does not support S3-compatible object storage

Options:

1. use an S3-compatible gateway
2. adapt `storage.py`
3. use provider-native SDK
4. split KFP artifacts and app artifacts intentionally

Document the choice in the provider overlay.

## Acceptance Criteria

You are done when:

- object storage check script exists
- local object storage check succeeds
- pod object storage check succeeds
- KFP pipeline root strategy is documented
- application artifact layout remains stable
- provider-native deviations are documented in the overlay

## References

- [Kubeflow Pipelines pipeline root](https://www.kubeflow.org/docs/components/pipelines/user-guides/data-handling/pipeline-root/)
- [Kubeflow Pipelines object store configuration](https://www.kubeflow.org/docs/components/pipelines/operator-guides/configure-object-store/)
- [boto3 S3 client documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)

## Next Step

Continue with [GPU and Node Pools](05-gpu-and-node-pools.md).
