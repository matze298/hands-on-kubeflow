# Run Flyte on k3s

The earlier Flyte pages run the workflow locally. That is useful for comparing authoring style, but it does not prove the workflow is Kubernetes-compatible.

This page turns the add-on into a real local platform path:

```text
repository checkout
  ->
k3s
  ->
Flyte backend in Kubernetes
  ->
Flyte task pods
  ->
local image
  ->
MinIO-backed artifact storage
```

This is still optional. The core tutorial remains Kubeflow Pipelines. The point here is to make the Flyte comparison fair: KFP ran on Kubernetes, so the Flyte add-on should have a Kubernetes-backed run as well.

## What You Will Build

You will create target files while following this page:

```text
infra/flyte/
├── postgres.yaml
└── k3s-values.yaml

flyte/
├── Dockerfile
└── kbd_flyte_workflow.py
```

The `kbd_flyte_workflow.py` file already exists from the local Flyte page. This page adds the backend and image pieces needed for remote execution.

## Prerequisites

You should already have:

- the `k3s-kubeflow` context from [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md)
- the tutorial MinIO service from [Install Local Object Storage](../04-artifacts-and-tracking/01-install-minio.md)
- the local Flyte workflow from [Local Flyte Workflow](02-local-flyte-workflow.md)
- `helm`, `kubectl`, `docker`, and `uv`

Verify the cluster:

```bash
kubectl config use-context k3s-kubeflow
kubectl get nodes
kubectl get pods -n kube-system
kubectl get pods -n minio
kubectl get svc -n minio
```

If MinIO is not installed, complete [Install Local Object Storage](../04-artifacts-and-tracking/01-install-minio.md) first. Flyte needs durable object storage for remote task data.

## Create the Flyte Namespace

```bash
kubectl create namespace flyte --dry-run=client -o yaml | kubectl apply -f -
```

Keep Flyte separate from:

```text
kubeflow            -> standalone KFP
kubeflow-by-doing   -> tutorial workloads
minio               -> local object storage
flyte               -> optional Flyte backend
```

That separation makes cleanup and debugging easier.

## Create a Local Postgres Database

The small Flyte backend needs a relational database for platform metadata. Create `infra/flyte/postgres.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: flyte-postgres
  namespace: flyte
type: Opaque
stringData:
  POSTGRES_PASSWORD: flyte
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: flyte-postgres
  namespace: flyte
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flyte-postgres
  namespace: flyte
  labels:
    app.kubernetes.io/name: flyte-postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: flyte-postgres
  template:
    metadata:
      labels:
        app.kubernetes.io/name: flyte-postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          env:
            - name: POSTGRES_DB
              value: flyte
            - name: POSTGRES_USER
              value: postgres
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: flyte-postgres
                  key: POSTGRES_PASSWORD
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          ports:
            - name: postgres
              containerPort: 5432
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: flyte-postgres
---
apiVersion: v1
kind: Service
metadata:
  name: flyte-postgres
  namespace: flyte
spec:
  selector:
    app.kubernetes.io/name: flyte-postgres
  ports:
    - name: postgres
      port: 5432
      targetPort: postgres
```

Apply it:

```bash
mkdir -p infra/flyte
kubectl apply -f infra/flyte/postgres.yaml
kubectl -n flyte rollout status deployment/flyte-postgres --timeout=120s
```

This is a local tutorial database, not a production database design.

## Configure Flyte for k3s

Flyte's platform deployment documentation presents Helm charts as the Kubernetes deployment path. For this local tutorial, use the small `flyte-binary` chart and point it at:

- the local Postgres service in the `flyte` namespace
- the existing MinIO service in the `minio` namespace
- the tutorial bucket `kubeflow-by-doing`
- unauthenticated local access through port forwarding

Create `infra/flyte/k3s-values.yaml`:

```yaml
flyte-core-components:
  runs:
    storagePrefix: s3://kubeflow-by-doing/flyte-data
    database:
      postgres:
        host: flyte-postgres.flyte.svc.cluster.local
        port: 5432
        dbname: flyte
        username: postgres
        password: flyte
        options: sslmode=disable
configuration:
  database:
    username: postgres
    password: flyte
    host: flyte-postgres.flyte.svc.cluster.local
    port: 5432
    dbname: flyte
    options: sslmode=disable
  storage:
    metadataContainer: kubeflow-by-doing
    userDataContainer: kubeflow-by-doing
    provider: s3
    providerConfig:
      s3:
        region: us-east-1
        endpoint: http://minio.minio.svc.cluster.local:9000
        disableSSL: true
        v2Signing: false
        authType: accesskey
        accessKey: minioadmin
        secretKey: minioadmin123
  auth:
    enabled: false
  inline:
    plugins:
      k8s:
        gpu-resource-name: nvidia.com/gpu
service:
  type: ClusterIP
console:
  service:
    type: ClusterIP
deployment:
  resources:
    requests:
      cpu: "250m"
      memory: "512Mi"
    limits:
      cpu: "2"
      memory: "2Gi"
```

!!! warning

    These credentials match the local MinIO chapter and are intentionally disposable. Do not use them outside a local tutorial cluster.

The `gpu-resource-name` value matches the Kubernetes extended resource exposed by the NVIDIA device plugin. Flyte's GPU documentation describes the same `nvidia.com/gpu` resource path.

The values set both the general Flyte storage/database keys and the `flyte-core-components.runs` keys used by the v2 `flyte-binary` chart. Keep those in sync when changing the local bucket or database service.

## Install the Flyte Backend

Install with Helm:

```bash
helm repo add flyteorg https://flyteorg.github.io/flyte --force-update
helm repo update

helm upgrade --install flyte flyteorg/flyte-binary \
  --namespace flyte \
  --create-namespace \
  -f infra/flyte/k3s-values.yaml
```

Wait for the backend:

```bash
kubectl -n flyte get pods
kubectl -n flyte rollout status deployment -l app.kubernetes.io/name=flyte-binary --timeout=180s
```

If the label selector does not match your chart version, inspect the objects directly:

```bash
kubectl -n flyte get deploy
kubectl -n flyte get svc
kubectl -n flyte describe pod <pod-name>
```

Chart names and labels can change. Keep the chapter pattern, but verify against the current Flyte chart when upgrading.

## Port-Forward the Flyte Backend

In one terminal, forward the backend API:

```bash
kubectl -n flyte port-forward svc/flyte-flyte-binary-http 8090:8090
```

Keep that terminal open.

If you also want to inspect the Flyte console, use a second terminal:

```bash
kubectl -n flyte port-forward svc/flyte-flyte-binary-console 8088:80
```

Then open:

```text
http://localhost:8088/v2
```

In another terminal, create a remote Flyte config:

```bash
mkdir -p .flyte/k3s-kubeflow
uv run flyte create config \
  --endpoint localhost:8090 \
  --insecure \
  --project kubeflow-by-doing \
  --domain development \
  --output .flyte/k3s-kubeflow/config.yaml \
  --force
```

The `.flyte/` directory remains machine-local and ignored by the repository.

Check connectivity:

```bash
uv run flyte --config .flyte/k3s-kubeflow/config.yaml get project
```

If the `kubeflow-by-doing` project does not exist, create it:

```bash
uv run flyte --config .flyte/k3s-kubeflow/config.yaml create project \
  --id kubeflow-by-doing \
  --name "Kubeflow by Doing" \
  --description "Local k3s Flyte project for the optional add-on."
```

## Build a Flyte Task Image

Remote Flyte tasks run in containers. Create `flyte/Dockerfile`:

```dockerfile
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PATH=/app/.venv/bin:$PATH

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY flyte ./flyte

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev
```

Build the image. Because the tutorial k3s cluster uses the host Docker runtime, the local image is available to k3s pods after the build:

```bash
export KBD_FLYTE_IMAGE=kubeflow-by-doing/flyte-cpu:local

docker build -f flyte/Dockerfile -t "$KBD_FLYTE_IMAGE" .
docker images "$KBD_FLYTE_IMAGE"
```

Verify that the cluster can pull the image:

```bash
kubectl -n kubeflow-by-doing run flyte-image-smoke \
  --image="$KBD_FLYTE_IMAGE" \
  --restart=Never \
  --command -- uv run python -c "import kubeflow_by_doing; print('ok')"

kubectl -n kubeflow-by-doing logs pod/flyte-image-smoke
kubectl -n kubeflow-by-doing delete pod flyte-image-smoke --ignore-not-found
```

If the image pull fails, confirm k3s was installed with the Docker runtime from Chapter 1 and that `docker images "$KBD_FLYTE_IMAGE"` shows the tag.

## Deploy the Flyte Environment

The local workflow page defined:

```python
env = flyte.TaskEnvironment(
    name="kubeflow-by-doing-flyte",
    image=flyte.Image.from_ref_name("kbd-flyte"),
    resources=flyte.Resources(cpu="1", memory="2Gi"),
)
```

Deploy that environment to the k3s Flyte backend:

```bash
export PYTHONPATH="$PWD/src"
export KBD_FLYTE_IMAGE=kubeflow-by-doing/flyte-cpu:local

uv run flyte --config .flyte/k3s-kubeflow/config.yaml deploy \
  --project kubeflow-by-doing \
  --domain development \
  --image kbd-flyte="$KBD_FLYTE_IMAGE" \
  flyte/kbd_flyte_workflow.py kubeflow-by-doing-flyte
```

The image mapping is the important part:

```text
kbd-flyte -> kubeflow-by-doing/flyte-cpu:local
```

That keeps the workflow source portable. Local execution can ignore the mapping; remote execution receives a concrete Kubernetes image.

## Run the Workflow Remotely

Submit a remote run:

```bash
uv run flyte --config .flyte/k3s-kubeflow/config.yaml run \
  --project kubeflow-by-doing \
  --domain development \
  --image kbd-flyte="$KBD_FLYTE_IMAGE" \
  --follow \
  flyte/kbd_flyte_workflow.py flyte_image_classification_pipeline \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --n-train 256 \
  --n-val 64 \
  --batch-size 32 \
  --min-accuracy 0.5
```

Now the work should run as Kubernetes pods, not only inside your local Python process.

Inspect the cluster while the run is active:

```bash
kubectl get pods -A | grep -i flyte
kubectl get events -A --sort-by=.lastTimestamp | tail -n 30
```

If you see task pods in a project/domain namespace created by Flyte, describe one:

```bash
kubectl describe pod <task-pod-name> -n <task-namespace>
kubectl logs <task-pod-name> -n <task-namespace>
```

## Add a GPU Task Later

Do not make the first k3s backend run require a GPU. First prove that:

- the backend starts
- the image pulls
- CPU tasks run
- MinIO credentials work
- logs are visible

After that, create a separate GPU task environment:

```python
gpu_env = flyte.TaskEnvironment(
    name="kubeflow-by-doing-flyte-gpu",
    image=flyte.Image.from_ref_name("kbd-flyte-gpu"),
    resources=flyte.Resources(cpu="2", memory="8Gi", gpu="T4:1"),
)
```

Then verify the cluster still advertises GPU capacity:

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

If that output is empty, fix the Chapter 1 k3s GPU path before debugging Flyte task code.

## Debug Common Failures

### Flyte backend pods do not start

Check Postgres, MinIO, and chart values:

```bash
kubectl -n flyte get pods
kubectl -n flyte describe pod <pod-name>
kubectl -n flyte logs <pod-name>
kubectl -n minio get svc
```

Common causes:

- Postgres is not ready
- the MinIO service name is wrong
- the bucket does not exist
- chart values changed between Flyte releases
- the local cluster does not have enough memory

### The CLI cannot connect

Confirm the port-forward is still running:

```bash
kubectl -n flyte get deploy
```

Then recreate the config:

```bash
uv run flyte create config \
  --endpoint localhost:8090 \
  --insecure \
  --project kubeflow-by-doing \
  --domain development \
  --output .flyte/k3s-kubeflow/config.yaml \
  --force
```

### Task pods cannot pull the image

Check the image name:

```bash
echo "$KBD_FLYTE_IMAGE"
```

It should be:

```text
kubeflow-by-doing/flyte-cpu:local
```

Then rebuild it and confirm Docker can see the tag:

```bash
docker build -f flyte/Dockerfile -t "$KBD_FLYTE_IMAGE" .
docker images "$KBD_FLYTE_IMAGE"
```

### Task pods cannot write artifacts

Check MinIO:

```bash
kubectl -n minio get pods
kubectl -n minio logs deployment/minio
```

Then verify the bucket from the Chapter 4 smoke test.

### GPU tasks stay pending

Describe the pod:

```bash
kubectl describe pod <task-pod-name> -n <task-namespace>
```

Look for:

- missing `nvidia.com/gpu`
- wrong GPU type
- insufficient GPU capacity
- taints without tolerations
- image CUDA/PyTorch mismatch

This is normal Kubernetes scheduling debugging. Flyte submits the work, but Kubernetes admits the pod.

## Cleanup

To remove only Flyte:

```bash
helm uninstall flyte -n flyte
kubectl delete namespace flyte --ignore-not-found
```

Do not delete `minio` unless you intentionally want to lose local tutorial artifacts.

To remove the local image tag:

```bash
docker rmi kubeflow-by-doing/flyte-cpu:local
```

## Acceptance Criteria

You are done when:

- `kubectl get pods -n flyte` shows the Flyte backend running
- `.flyte/k3s-kubeflow/config.yaml` points at the local Flyte backend
- `uv run flyte --config .flyte/k3s-kubeflow/config.yaml get project` works
- `docker images kubeflow-by-doing/flyte-cpu:local` shows the local task image
- `flyte/kbd_flyte_workflow.py` deploys with the `kbd-flyte` image mapping
- the workflow can be submitted to the k3s Flyte backend
- you can find the resulting Flyte task pods with `kubectl`
- you can explain how this differs from `uv run flyte run --local`

## References

- [Flyte platform deployment](https://www.union.ai/docs/v2/flyte/deployment/)
- [Flyte GPU access configuration](https://www.union.ai/docs/v2/flyte/deployment/flyte-configuration/configuring-access-to-gpus/)
- [Flyte resources](https://www.union.ai/docs/v2/flyte/user-guide/configure-tasks/resources/)
- [Flyte secrets](https://www.union.ai/docs/v2/flyte/user-guide/configure-tasks/secrets/)
- [k3s documentation](https://docs.k3s.io/)

## End of Add-On

You have reached the end of the optional Flyte track. Return to [Conclusion and Future Reading](../11-conclusion/00-overview.md) when you want the broader Kubeflow and MLOps reading list.
