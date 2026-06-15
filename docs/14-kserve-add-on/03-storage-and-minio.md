# Storage and MinIO

This page connects KServe to the local MinIO object store from Chapter 4.

KServe has a storage initializer that downloads model artifacts before the predictor container starts. For S3-compatible storage, the initializer needs endpoint and credential configuration.

## What You Will Build

You will create:

```text
infra/kserve/
├── minio-secret.yaml
└── service-account.yaml
```

The service account will be used by KServe predictor pods that need to read from:

```text
s3://kubeflow-by-doing/...
```

## Prerequisites

MinIO must be running:

```bash
kubectl -n minio get pods
kubectl -n minio get svc minio
```

The tutorial bucket must exist:

```bash
kubectl -n minio port-forward svc/minio 9000:9000
```

In another terminal:

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export AWS_DEFAULT_REGION=us-east-1
export KBD_S3_ENDPOINT_URL=http://localhost:9000
export KBD_ARTIFACT_BUCKET=kubeflow-by-doing
```

Then verify the bucket:

```bash
uv run python - <<'PY'
import os

import boto3
from botocore.client import Config

client = boto3.client(
    "s3",
    endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    config=Config(signature_version="s3v4"),
)

bucket = os.environ["KBD_ARTIFACT_BUCKET"]
names = [item["Name"] for item in client.list_buckets()["Buckets"]]
print(f"{bucket} exists: {bucket in names}")
PY
```

## Create the KServe S3 Secret

Create `infra/kserve/minio-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kserve-minio-credentials
  namespace: kubeflow-by-doing
  annotations:
    serving.kserve.io/s3-endpoint: minio.minio.svc.cluster.local:9000
    serving.kserve.io/s3-usehttps: "0"
    serving.kserve.io/s3-region: us-east-1
    serving.kserve.io/s3-useanoncredential: "false"
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: minioadmin
  AWS_SECRET_ACCESS_KEY: minioadmin123
```

The annotations are the important difference from the Chapter 4 application secret. KServe reads these annotations to configure the storage initializer.

Apply:

```bash
kubectl apply -f infra/kserve/minio-secret.yaml
```

## Create the KServe Service Account

Create `infra/kserve/service-account.yaml`:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kserve-minio-reader
  namespace: kubeflow-by-doing
secrets:
  - name: kserve-minio-credentials
```

Apply:

```bash
kubectl apply -f infra/kserve/service-account.yaml
```

Verify:

```bash
kubectl -n kubeflow-by-doing get secret kserve-minio-credentials
kubectl -n kubeflow-by-doing get serviceaccount kserve-minio-reader -o yaml
```

## Storage URI Rules

KServe `storageUri` should point to a directory or model repository, not just an arbitrary file, unless the selected runtime explicitly documents file-level behavior.

For this tutorial:

```text
s3://kubeflow-by-doing/runs/<run_id>/models/
```

is preferred over:

```text
s3://kubeflow-by-doing/runs/<run_id>/models/model.pt
```

The storage initializer downloads the model directory into:

```text
/mnt/models
```

The custom predictor in the next page will load:

```text
/mnt/models/model.pt
```

## Quick Credential Debug Pod

Before involving KServe, verify that a pod in the tutorial namespace can read from MinIO:

```bash
kubectl -n kubeflow-by-doing run s3-check \
  --image=python:3.12-slim \
  --restart=Never \
  --env=AWS_ACCESS_KEY_ID=minioadmin \
  --env=AWS_SECRET_ACCESS_KEY=minioadmin123 \
  --env=AWS_DEFAULT_REGION=us-east-1 \
  --env=KBD_S3_ENDPOINT_URL=http://minio.minio.svc.cluster.local:9000 \
  --env=KBD_ARTIFACT_BUCKET=kubeflow-by-doing \
  -- /bin/sh -c 'pip install --no-cache-dir boto3 >/dev/null && python - <<PY
import os
import boto3
from botocore.client import Config
client = boto3.client(
    "s3",
    endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name=os.environ["AWS_DEFAULT_REGION"],
    config=Config(signature_version="s3v4"),
)
print(client.list_objects_v2(Bucket=os.environ["KBD_ARTIFACT_BUCKET"], MaxKeys=5))
PY'
```

Read logs and clean up:

```bash
kubectl -n kubeflow-by-doing logs pod/s3-check
kubectl -n kubeflow-by-doing delete pod s3-check --ignore-not-found
```

## Common Problems

### Storage initializer cannot connect

Check the endpoint annotation:

```text
minio.minio.svc.cluster.local:9000
```

Do not use `localhost:9000` inside the cluster. `localhost` would point at the predictor pod, not your laptop.

### Storage initializer uses HTTPS

For local MinIO, keep:

```yaml
serving.kserve.io/s3-usehttps: "0"
```

Use HTTPS only when the object store is configured for it and the certificate trust path is handled.

### Secret exists but KServe ignores it

Verify that the `InferenceService` uses:

```yaml
serviceAccountName: kserve-minio-reader
```

The secret must be attached to the service account used by the predictor.

## Acceptance Criteria

You are done when:

- `kserve-minio-credentials` exists
- `kserve-minio-reader` references that secret
- a debug pod can list objects in the tutorial bucket
- you understand why KServe uses annotated storage credentials instead of only normal application env vars

## References

- [KServe S3 storage provider](https://kserve.github.io/website/docs/model-serving/storage/providers/s3)
- [KServe model storage overview](https://kserve.github.io/website/docs/model-serving/storage/overview)

## Next Step

Continue with [Serve the Tutorial Model](04-serve-the-tutorial-model.md).
