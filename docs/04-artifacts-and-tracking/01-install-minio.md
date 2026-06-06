# Install Local Object Storage

This page installs MinIO as local S3-compatible object storage in Kubernetes.

## What You Will Build

You will create:

```text
infra/minio/
├── namespace.yaml
├── secret.yaml
├── pvc.yaml
├── deployment.yaml
└── service.yaml
```

Then you will create a bucket:

```text
s3://kubeflow-by-doing
```

## Why This Matters

A Kubernetes pod is temporary.

If a training component writes a model only to the pod filesystem, the artifact is not a durable platform artifact.

Object storage gives us a stable place for datasets, trained models, metrics, reports, lineage records, and predictions.

Locally, MinIO gives us an S3-compatible API. Later, the same code can point to STACKIT object storage, AWS S3, or another S3-compatible backend.

## Create the MinIO Namespace

Create `infra/minio/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: minio
```

Apply:

```bash
mkdir -p infra/minio
kubectl apply -f infra/minio/namespace.yaml
```

## Create MinIO Credentials

Create `infra/minio/secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: minio-root-credentials
  namespace: minio
type: Opaque
stringData:
  MINIO_ROOT_USER: minioadmin
  MINIO_ROOT_PASSWORD: minioadmin123
```

!!! warning

    These credentials are intentionally simple for local development. Do not use them outside a disposable local tutorial cluster.

Apply:

```bash
kubectl apply -f infra/minio/secret.yaml
```

## Create Persistent Storage

Create `infra/minio/pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-data
  namespace: minio
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

Apply:

```bash
kubectl apply -f infra/minio/pvc.yaml
```

## Create the MinIO Deployment

Create `infra/minio/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minio
  namespace: minio
  labels:
    app.kubernetes.io/name: minio
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: minio
  template:
    metadata:
      labels:
        app.kubernetes.io/name: minio
    spec:
      containers:
        - name: minio
          image: quay.io/minio/minio:RELEASE.2025-05-24T17-08-30Z
          args:
            - server
            - /data
            - --console-address
            - ":9001"
          envFrom:
            - secretRef:
                name: minio-root-credentials
          ports:
            - name: api
              containerPort: 9000
            - name: console
              containerPort: 9001
          volumeMounts:
            - name: data
              mountPath: /data
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: minio-data
```

Apply:

```bash
kubectl apply -f infra/minio/deployment.yaml
kubectl -n minio rollout status deployment/minio --timeout=120s
```

## Create Services

Create `infra/minio/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: minio
  namespace: minio
  labels:
    app.kubernetes.io/name: minio
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: minio
  ports:
    - name: api
      port: 9000
      targetPort: api
    - name: console
      port: 9001
      targetPort: console
```

Apply:

```bash
kubectl apply -f infra/minio/service.yaml
```

## Verify MinIO

```bash
kubectl -n minio get pods
kubectl -n minio get svc
kubectl -n minio logs deployment/minio
```

## Access the MinIO Console

Port-forward the console:

```bash
kubectl -n minio port-forward svc/minio 9001:9001
```

Open:

```text
http://localhost:9001
```

Login:

```text
Username: minioadmin
Password: minioadmin123
```

## Access the S3 API Locally

In a second terminal:

```bash
kubectl -n minio port-forward svc/minio 9000:9000
```

The local S3 endpoint is:

```text
http://localhost:9000
```

Inside the Kubernetes cluster, the endpoint is:

```text
http://minio.minio.svc.cluster.local:9000
```

## Create the Tutorial Bucket

Add the S3 client dependency:

```bash
uv add boto3
```

Create the bucket through the local port-forward:

```bash
uv run python - <<'PY'
import boto3
from botocore.client import Config

endpoint_url = "http://localhost:9000"
bucket = "kubeflow-by-doing"

s3 = boto3.client(
    "s3",
    endpoint_url=endpoint_url,
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin123",
    config=Config(signature_version="s3v4"),
)

existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]
if bucket not in existing:
    s3.create_bucket(Bucket=bucket)

print(f"bucket ready: s3://{bucket}")
PY
```

## Create an Application Secret for Pipeline Pods

Pipeline pods need S3 credentials too.

Create `infra/minio/app-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: artifact-store-credentials
  namespace: kubeflow-by-doing
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: minioadmin
  AWS_SECRET_ACCESS_KEY: minioadmin123
  AWS_DEFAULT_REGION: us-east-1
  MLFLOW_S3_ENDPOINT_URL: http://minio.minio.svc.cluster.local:9000
  KBD_S3_ENDPOINT_URL: http://minio.minio.svc.cluster.local:9000
  KBD_ARTIFACT_BUCKET: kubeflow-by-doing
```

Apply:

```bash
kubectl apply -f infra/minio/app-secret.yaml
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
```

## Common Problems

### Console works, but Python cannot connect

The console uses port `9001`. The S3 API uses port `9000`.

Make sure this is running:

```bash
kubectl -n minio port-forward svc/minio 9000:9000
```

### Pipeline pod cannot connect to MinIO

Inside Kubernetes, do not use `localhost`.

Use:

```text
http://minio.minio.svc.cluster.local:9000
```

### Secret is in the wrong namespace

Pipeline pods run in the tutorial namespace, so the application secret must exist in:

```text
kubeflow-by-doing
```

## Cleanup

```bash
kubectl delete -f infra/minio/app-secret.yaml --ignore-not-found
kubectl delete -f infra/minio/service.yaml --ignore-not-found
kubectl delete -f infra/minio/deployment.yaml --ignore-not-found
kubectl delete -f infra/minio/pvc.yaml --ignore-not-found
kubectl delete -f infra/minio/secret.yaml --ignore-not-found
kubectl delete -f infra/minio/namespace.yaml --ignore-not-found
```

This deletes local object storage and the artifacts stored in it.

## Acceptance Criteria

You are done when:

- `kubectl -n minio get pods` shows MinIO running
- the MinIO console opens at `http://localhost:9001`
- the S3 API is reachable at `http://localhost:9000`
- the bucket `kubeflow-by-doing` exists
- `artifact-store-credentials` exists in the `kubeflow-by-doing` namespace

## References

- [MinIO Kubernetes documentation](https://docs.min.io/)
- [MinIO Python SDK](https://minio-py.min.io/)
- [boto3 S3 client documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## Next Step

Continue with [Define Artifact Layout](02-artifact-layout.md).
