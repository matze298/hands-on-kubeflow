# Create a Local Kubernetes Cluster

In this page, you create the local Kubernetes cluster used for the rest of the tutorial.

We use `kind` as the default cluster backend.

If you want Kubernetes-level GPU scheduling locally, this page also shows an optional `minikube` profile that is better aligned with NVIDIA GPU passthrough.

## What You Will Build

You will create a local cluster named:

```text
kubeflow-by-doing
```

You will also create a namespace named:

```text
kubeflow-by-doing
```

The cluster is disposable. If it breaks, delete it and recreate it.

## Why This Matters

Kubeflow workloads run inside Kubernetes.

A local cluster gives you a cheap, fast, and inspectable place to learn:

- how workloads are scheduled
- how containers run
- how logs are collected
- how services are exposed
- how failures appear
- how Kubeflow later maps pipelines to pods

## Create a kind Config

Create this file:

```bash
mkdir -p infra/kind
cat > infra/kind/kubeflow-by-doing.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: kubeflow-by-doing
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30080
        hostPort: 8080
        protocol: TCP
      - containerPort: 30443
        hostPort: 8443
        protocol: TCP
  - role: worker
EOF
```

This creates:

- one control-plane node
- one worker node
- two optional port mappings for later local services

This is the default CPU-safe baseline cluster for the tutorial.

## Create the Cluster

```bash
kind create cluster --config infra/kind/kubeflow-by-doing.yaml
```

Verify:

```bash
kubectl cluster-info
kubectl get nodes -o wide
```

Expected result:

```text
NAME                              STATUS   ROLES           AGE   VERSION
kubeflow-by-doing-control-plane   Ready    control-plane   ...
kubeflow-by-doing-worker          Ready    <none>          ...
```

## Optional: Create a GPU-Capable Local Cluster

If you want Kubernetes pods to request `nvidia.com/gpu` locally, create a small `minikube` launcher instead of trying to retrofit GPU passthrough into the default `kind` cluster.

`minikube` is another local Kubernetes backend. Unlike the default `kind` setup in this tutorial, it has an official GPU-oriented path for local development and can manage the Kubernetes node runtime in a way that is friendlier to NVIDIA GPU passthrough.

In practice, this optional path does three things:

- starts a separate local cluster profile just for GPU work
- asks the local cluster runtime to expose all visible GPUs to Kubernetes
- enables the NVIDIA device plugin addon so the node can advertise `nvidia.com/gpu`

Create this file:

```bash
mkdir -p infra/minikube
cat > infra/minikube/start-gpu-cluster.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

PROFILE="${MINIKUBE_PROFILE:-kubeflow-by-doing-gpu}"
CPUS="${MINIKUBE_CPUS:-8}"
MEMORY="${MINIKUBE_MEMORY:-8162}"

minikube start \
  --profile "$PROFILE" \
  --driver docker \
  --container-runtime docker \
  --gpus all \
  --cpus "$CPUS" \
  --memory "$MEMORY"

minikube addons enable nvidia-device-plugin --profile "$PROFILE"
EOF

chmod +x infra/minikube/start-gpu-cluster.sh
```

This script:

- creates a separate `minikube` profile named `kubeflow-by-doing-gpu`
- uses the Docker driver and Docker container runtime
- requests all visible GPUs for the local cluster
- enables the NVIDIA device plugin addon after the cluster starts

Command details:

- `--profile "$PROFILE"` keeps the GPU-capable cluster separate from the default `kind` flow
- `--driver docker` tells `minikube` to run the cluster on top of Docker
- `--container-runtime docker` keeps the runtime aligned with the NVIDIA Container Toolkit setup from the toolchain chapter
- `--gpus all` asks the local cluster to expose every visible GPU to the Kubernetes node
- `--cpus` and `--memory` reserve enough local resources for the cluster and the later Kubeflow workloads
- `minikube addons enable nvidia-device-plugin` installs the device plugin addon after the cluster is up

Then start the GPU-ready profile:

```bash
bash infra/minikube/start-gpu-cluster.sh
```

Verify:

```bash
kubectl config current-context
kubectl get nodes -o wide
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

Expected result:

- the current context is `kubeflow-by-doing-gpu` or can be switched to it with `kubectl config use-context kubeflow-by-doing-gpu`
- at least one node reports a non-empty `allocatable gpu=` value

If `allocatable gpu=` is blank, stop the GPU path here and debug the `minikube` GPU setup before moving on to pod specs or Kubeflow GPU workloads.

## Create the Tutorial Namespace

Before creating the namespace, make sure `kubectl` points at the cluster you want to prepare:

- use `kind-kubeflow-by-doing` for the default core path
- use `kubeflow-by-doing-gpu` for the optional GPU-capable path

```bash
kubectl create namespace kubeflow-by-doing
```

Set it as the default namespace for the current context:

```bash
kubectl config set-context --current --namespace=kubeflow-by-doing
```

Verify:

```bash
kubectl config view --minify --output 'jsonpath={..namespace}'
echo
```

Expected output:

```text
kubeflow-by-doing
```

## Inspect the Cluster

Show all pods:

```bash
kubectl get pods -A
```

Show namespaces:

```bash
kubectl get namespaces
```

Show node details:

```bash
kubectl describe nodes
```

You do not need to understand every line. For now, notice:

- node names
- allocatable CPU and memory
- labels
- conditions
- events

## Optional: Create a Basic Resource Quota

A local cluster can still be overwhelmed. Add a small quota to make resource use explicit:

Create this file:

```bash
cat > infra/kind/kubeflow-by-doing-quota.yaml <<'EOF'
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tutorial-quota
  namespace: kubeflow-by-doing
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "50"
EOF
```

Then apply it:

```bash
kubectl apply -f infra/kind/kubeflow-by-doing-quota.yaml
```

Verify:

```bash
kubectl describe resourcequota tutorial-quota
```

If your machine has less memory, adjust the quota or skip this step.

If you are working on the optional GPU-capable `minikube` profile, apply the same namespace and quota manifests there after switching context.

## Common Problems

### `kind create cluster` fails because the name already exists

Delete the old cluster:

```bash
kind delete cluster --name kubeflow-by-doing
```

Then recreate it:

```bash
kind create cluster --config infra/kind/kubeflow-by-doing.yaml
```

### `kubectl get nodes` points to the wrong cluster

List contexts:

```bash
kubectl config get-contexts
```

Switch to the kind context:

```bash
kubectl config use-context kind-kubeflow-by-doing
```

### Nodes stay `NotReady`

Check all pods:

```bash
kubectl get pods -A
```

Then inspect node events:

```bash
kubectl describe nodes
```

For local clusters, the fastest fix is often to delete and recreate.

### Docker is out of resources

Increase Docker Desktop or Docker daemon resources.

As a practical default, reserve at least:

```text
CPU: 8 cores if possible
Memory: 16 GiB minimum, 24–32 GiB better
Disk: 50+ GiB free
```

### The default `kind` cluster cannot request GPUs

That is expected. The default `kind` cluster is the baseline path for the Kubernetes and Kubeflow basics.

If you want local Kubernetes GPU scheduling, use the optional `minikube` GPU profile from this page instead of continuing to debug `kind` node runtime wiring.

## Cleanup

To delete the cluster:

```bash
kind delete cluster --name kubeflow-by-doing
```

To delete the optional GPU-ready profile:

```bash
minikube delete --profile kubeflow-by-doing-gpu
```

Do not delete it yet if you are continuing the tutorial.

## What You Learned

You created a local Kubernetes cluster and a namespace for tutorial workloads.

You also learned that local Kubernetes should be treated as disposable infrastructure.

You also saw that the tutorial separates the default `kind` baseline from the optional GPU-capable `minikube` path.

## References

- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [kind configuration](https://kind.sigs.k8s.io/docs/user/configuration/)
- [minikube start](https://minikube.sigs.k8s.io/docs/start/)
- [Using NVIDIA GPUs with minikube](https://minikube.sigs.k8s.io/docs/tutorials/nvidia/)
- [Kubernetes namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
- [Kubernetes resource quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)

## Acceptance Criteria

You are done when:

- `kubectl get nodes` shows ready nodes
- `kubectl config view --minify` points to the cluster you are preparing
- the default namespace is `kubeflow-by-doing`
- `kubectl get pods -A` works
- you know how to delete and recreate the cluster
- if you choose the optional GPU-ready path, `kubectl get nodes -o jsonpath=...` shows a non-empty `nvidia.com/gpu`

## Next Step

Continue with [First Kubernetes Job](03-first-kubernetes-job.md).
