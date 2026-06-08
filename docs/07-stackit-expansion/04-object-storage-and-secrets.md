# Object Storage and Secrets

This page replaces local MinIO with STACKIT Object Storage.

## What You Will Build

You will create:

```text
scripts/stackit-create-object-bucket.py
scripts/stackit-verify-artifacts.py
infra/stackit/object-storage-secret.yaml
```

## Why This Matters

The pipeline should keep the same artifact layout while changing only the storage backend.

Local:

```text
endpoint: http://minio.minio.svc.cluster.local:9000
bucket:   kubeflow-by-doing
```

STACKIT:

```text
endpoint: <STACKIT Object Storage S3 endpoint>
bucket:   kubeflow-by-doing
```

The code from Chapter 4 already supports this because it uses S3-compatible configuration from environment variables.

## Create or Select a Bucket

Use the STACKIT Portal, `s3cmd`, AWS-compatible tooling, or Python with `boto3`.

The bucket name in this tutorial is:

```text
kubeflow-by-doing
```

If the name is globally unavailable in your project or region, choose a unique name and update:

```bash
export KBD_ARTIFACT_BUCKET="<your-unique-bucket>"
```

## Create `scripts/stackit-create-object-bucket.py`

```python
from __future__ import annotations

import os

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
        region_name=os.environ.get("AWS_DEFAULT_REGION", "eu01"),
        config=Config(signature_version="s3v4"),
    )

    existing = [item["Name"] for item in client.list_buckets()["Buckets"]]
    if bucket not in existing:
        client.create_bucket(Bucket=bucket)

    print(f"bucket ready: s3://{bucket}")


if __name__ == "__main__":
    main()
```

Run:

```bash
uv add boto3
source .env.stackit
uv run python scripts/stackit-create-object-bucket.py
```

## Create the Kubernetes Secret

Create `infra/stackit/object-storage-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: artifact-store-credentials
  namespace: kubeflow-by-doing
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: <replace-with-access-key-id>
  AWS_SECRET_ACCESS_KEY: <replace-with-secret-access-key>
  AWS_DEFAULT_REGION: eu01
  KBD_S3_ENDPOINT_URL: <replace-with-stackit-object-storage-endpoint>
  KBD_ARTIFACT_BUCKET: kubeflow-by-doing
  MLFLOW_S3_ENDPOINT_URL: <replace-with-stackit-object-storage-endpoint>
  MLFLOW_TRACKING_URI: http://mlflow.kubeflow-by-doing.svc.cluster.local:5000
  MLFLOW_EXPERIMENT_NAME: kubeflow-by-doing-stackit
```

!!! warning

    This file contains secrets if filled directly. For real projects, use sealed secrets, external secrets, or a secret manager. For the tutorial, Codex can generate this file locally but it should not be committed with real values.

Apply:

```bash
kubectl apply -f infra/stackit/object-storage-secret.yaml
```

Verify:

```bash
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
```

## Verify Artifact Access from Your Laptop

Create `scripts/stackit-verify-artifacts.py`:

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
        region_name=os.environ.get("AWS_DEFAULT_REGION", "eu01"),
        config=Config(signature_version="s3v4"),
    )

    probe_path = Path("outputs/stackit-artifact-probe.txt")
    probe_path.parent.mkdir(parents=True, exist_ok=True)
    probe_path.write_text("hello stackit object storage\n", encoding="utf-8")

    key = "reports/stackit-artifact-probe.txt"
    client.upload_file(str(probe_path), bucket, key)

    response = client.list_objects_v2(Bucket=bucket, Prefix="reports/")
    for item in response.get("Contents", []):
        print(f"s3://{bucket}/{item['Key']}")


if __name__ == "__main__":
    main()
```

Run:

```bash
source .env.stackit
uv run python scripts/stackit-verify-artifacts.py
```

## Verify Artifact Access from Kubernetes

Create `infra/stackit/object-storage-smoke.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: object-storage-smoke
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  containers:
    - name: smoke
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
              region_name=os.environ.get("AWS_DEFAULT_REGION", "eu01"),
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
kubectl apply -f infra/stackit/object-storage-smoke.yaml
kubectl -n kubeflow-by-doing logs pod/object-storage-smoke
kubectl -n kubeflow-by-doing delete pod object-storage-smoke --ignore-not-found
```

## Common Problems

### Signature or authentication error

Check that STACKIT Object Storage credentials are correct and that your client uses Signature V4.

### Pod can access DNS but not object storage

Check endpoint URL, network policies, and whether the object storage endpoint is reachable from SKE nodes.

### Bucket exists locally but not in STACKIT

You are probably still pointing at MinIO.

Check:

```bash
echo "$KBD_S3_ENDPOINT_URL"
```

## Acceptance Criteria

You are done when:

- object storage bucket exists
- laptop can upload and list an object
- SKE pod can list objects using the Kubernetes Secret
- the secret uses the same key names expected by Chapter 4 code
- artifact layout remains `s3://<bucket>/runs/<run_id>/...`

## References

- [STACKIT Object Storage documentation](https://docs.stackit.cloud/products/storage/object-storage/)
- [STACKIT Object Storage basic operations](https://docs.stackit.cloud/products/storage/object-storage/how-tos/basic-operations-object-storage/)
- [Supported S3 operations](https://docs.stackit.cloud/products/storage/object-storage/reference/supported-operations-on-buckets-and-objects/)

## Next Step

Continue with [Run KFP on STACKIT](05-run-kfp-on-stackit.md).
