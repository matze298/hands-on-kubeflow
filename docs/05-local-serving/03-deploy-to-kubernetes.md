# Deploy to Kubernetes

This page deploys the model server into the local Kubernetes cluster.

## What You Will Build

You will create:

```text
manifests/model-server/
├── configmap.yaml
├── deployment.yaml
└── service.yaml
```

The server will:

1. download `model.pt` from MinIO using an init container
2. mount it into the FastAPI container
3. expose `/healthz` and `/predict` through a Kubernetes `Service`

## Why This Matters

A model server in Kubernetes is not just a Python process.

It is a managed workload:

```text
Deployment
  ↓
Pod
  ├── init container downloads model
  ├── app container serves model
  ├── shared volume stores model file
  └── Service exposes endpoint inside the cluster
```

This is the simplest transparent serving pattern before introducing KServe.

## Prerequisites

You need:

- MinIO running
- a trained model uploaded to MinIO
- the serving image loaded into the default `minikube` cluster, or into `kind` if you are using the fallback path
- the `artifact-store-credentials` Secret from Chapter 4

Use a known run ID:

```bash
export RUN_ID=manual-local-001
```

If you need to upload a model first, port-forward MinIO:

```bash
kubectl -n minio port-forward svc/minio 9000:9000
```

Then in another terminal:

```bash
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin123
export AWS_DEFAULT_REGION=us-east-1
export KBD_S3_ENDPOINT_URL=http://localhost:9000
export KBD_ARTIFACT_BUCKET=kubeflow-by-doing

mkdir -p outputs/serve-train

uv run kbd train-model \
  --output-dir outputs/serve-train \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --device cpu \
  --run-id "$RUN_ID" \
  --upload-artifacts
```

Expected model URI:

```text
s3://kubeflow-by-doing/runs/manual-local-001/models/model.pt
```

## Create the Folder

```bash
mkdir -p manifests/model-server
```

## Create the ConfigMap

Create `manifests/model-server/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: model-server-config
  namespace: kubeflow-by-doing
data:
  KBD_MODEL_S3_URI: s3://kubeflow-by-doing/runs/manual-local-001/models/model.pt
  KBD_MODEL_PATH: /models/model.pt
  KBD_SERVE_DEVICE: cpu
```

!!! note

    Later, the pipeline will update the model URI or generate this manifest. For now, we use a fixed run ID to make serving concrete.

## Verify the Secret

The server uses the Chapter 4 `artifact-store-credentials` Secret.

Verify:

```bash
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
```

## Create the Deployment

Create `manifests/model-server/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-server
  namespace: kubeflow-by-doing
  labels:
    app.kubernetes.io/name: model-server
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: model-server
  template:
    metadata:
      labels:
        app.kubernetes.io/name: model-server
    spec:
      initContainers:
        - name: download-model
          image: python:3.12-slim
          command:
            - /bin/sh
            - -c
            - |
              pip install --no-cache-dir boto3 &&
              python - <<'PY'
              import os
              from pathlib import Path
              from urllib.parse import urlparse

              import boto3
              from botocore.client import Config

              model_uri = os.environ["KBD_MODEL_S3_URI"]
              model_path = Path(os.environ["KBD_MODEL_PATH"])
              model_path.parent.mkdir(parents=True, exist_ok=True)

              parsed = urlparse(model_uri)
              bucket = parsed.netloc
              key = parsed.path.lstrip("/")

              client = boto3.client(
                  "s3",
                  endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
                  aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                  aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                  region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                  config=Config(signature_version="s3v4"),
              )
              client.download_file(bucket, key, str(model_path))
              print(f"downloaded {model_uri} to {model_path}")
              PY
          envFrom:
            - configMapRef:
                name: model-server-config
            - secretRef:
                name: artifact-store-credentials
          volumeMounts:
            - name: model-volume
              mountPath: /models
      containers:
        - name: server
          image: kubeflow-by-doing/serve:local
          imagePullPolicy: IfNotPresent
          envFrom:
            - configMapRef:
                name: model-server-config
          ports:
            - name: http
              containerPort: 8000
          readinessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
          volumeMounts:
            - name: model-volume
              mountPath: /models
              readOnly: true
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
      volumes:
        - name: model-volume
          emptyDir: {}
```

## Create the Service

Create `manifests/model-server/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: model-server
  namespace: kubeflow-by-doing
  labels:
    app.kubernetes.io/name: model-server
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: model-server
  ports:
    - name: http
      port: 8000
      targetPort: http
```

## Load the Serving Image into the Cluster

```bash
mkdir -p build
docker save kubeflow-by-doing/serve:local > build/serve-image.tar
minikube image load kubeflow-by-doing/serve:local -p kubeflow-gpu
```

If you are using the `kind` fallback path, load it with:

```bash
kind load docker-image kubeflow-by-doing/serve:local --name kubeflow-by-doing
```

## Apply the Manifests

```bash
kubectl apply -f manifests/model-server/configmap.yaml
kubectl apply -f manifests/model-server/deployment.yaml
kubectl apply -f manifests/model-server/service.yaml
```

Wait:

```bash
kubectl -n kubeflow-by-doing rollout status deployment/model-server --timeout=120s
```

## Inspect the Pod

```bash
kubectl -n kubeflow-by-doing get pods -l app.kubernetes.io/name=model-server
kubectl -n kubeflow-by-doing logs deployment/model-server -c download-model
kubectl -n kubeflow-by-doing logs deployment/model-server -c server
```

## Port-Forward the Service

```bash
kubectl -n kubeflow-by-doing port-forward svc/model-server 8000:8000
```

## Check Health

```bash
curl http://localhost:8000/healthz
```

## Send a Prediction

```bash
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

## Common Problems

### Init container cannot download the model

Inspect init-container logs:

```bash
kubectl -n kubeflow-by-doing logs deployment/model-server -c download-model
```

Check:

- `KBD_MODEL_S3_URI`
- MinIO endpoint
- bucket name
- object key
- credentials
- secret namespace

### `ImagePullBackOff`

The serving image may not be loaded into the active local cluster. Re-run the image load step above, then retry the deployment.

### Readiness probe fails

Check server logs:

```bash
kubectl -n kubeflow-by-doing logs deployment/model-server -c server
```

Most likely causes:

- model load failed
- wrong model path
- incompatible checkpoint
- app import failed

## Cleanup

```bash
kubectl delete -f manifests/model-server/service.yaml --ignore-not-found
kubectl delete -f manifests/model-server/deployment.yaml --ignore-not-found
kubectl delete -f manifests/model-server/configmap.yaml --ignore-not-found
```

## Acceptance Criteria

You are done when:

- `model-server` deployment exists
- the init container downloads the model from MinIO
- the server container becomes ready
- `svc/model-server` exists
- `/healthz` works through port forwarding
- `/predict` works through port forwarding

## References

- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes init containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [Kubernetes probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## Next Step

Continue with [Connect Pipeline to Serving](04-connect-pipeline-to-serving.md).
