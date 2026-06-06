# Create a Local Kubernetes Cluster

In this page, you create the local Kubernetes cluster used for the rest of the tutorial.

We use `kind` as the starter cluster backend for the initial Kubernetes exercises.

If you want Kubernetes-level GPU scheduling locally on WSL2, this page also shows the `MicroK8s` path that becomes the default local ML platform for the later chapters.

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

This is the starter CPU-safe baseline cluster for the tutorial.

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

## Create the GPU-Capable Local Cluster

If you want Kubernetes pods to request `nvidia.com/gpu` locally on WSL2, use `MicroK8s` instead of trying to retrofit GPU passthrough into the `kind` starter cluster.

`MicroK8s` runs natively inside the WSL2 Ubuntu environment and has official WSL2 installation and GPU addon documentation. That is the GPU-capable local cluster path used in the rest of the tutorial.

In practice, this optional path does four things:

- starts a local Kubernetes cluster inside WSL2
- enables DNS and storage so later Kubeflow services can start cleanly
- enables the built-in registry so locally built images can be imported or pushed consistently
- enables the GPU addon so the node can advertise `nvidia.com/gpu`

Create this file:

```bash
mkdir -p infra/microk8s
cat > infra/microk8s/bootstrap-gpu-cluster.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

sudo microk8s status --wait-ready
sudo microk8s enable dns storage registry
sudo microk8s enable gpu --gpu-operator-set-as-default-runtime

mkdir -p "$HOME/.kube"
sudo microk8s config > "$HOME/.kube/microk8s-config"

if [ -f "$HOME/.kube/config" ]; then
  KUBECONFIG="$HOME/.kube/config:$HOME/.kube/microk8s-config" kubectl config view --flatten > "$HOME/.kube/config.merged"
  mv "$HOME/.kube/config.merged" "$HOME/.kube/config"
else
  cp "$HOME/.kube/microk8s-config" "$HOME/.kube/config"
fi

kubectl config use-context microk8s
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace=kubeflow-by-doing

kubectl get nodes -o wide
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
EOF

chmod +x infra/microk8s/bootstrap-gpu-cluster.sh
```

This script:

- waits for `MicroK8s` to be ready
- enables the `dns`, `storage`, and `registry` addons needed later
- enables the GPU addon and asks it to set the NVIDIA runtime as the default runtime for workloads
- exports the `microk8s` kubeconfig into your normal `kubectl` config
- switches the current context to `microk8s`
- creates the tutorial namespace and sets it as the default namespace for that context

Then bootstrap the GPU-ready cluster:

```bash
bash infra/microk8s/bootstrap-gpu-cluster.sh
```

Verify:

```bash
kubectl config current-context
kubectl get pods -n kube-system
kubectl get pods -n gpu-operator-resources
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

Expected result:

- the current context is `microk8s`
- core `kube-system` pods are `Running`
- GPU operator pods in `gpu-operator-resources` are mostly `Running` or `Completed`
- at least one node reports a non-empty `allocatable gpu=` value

If `kube-system` is unhealthy or `allocatable gpu=` is blank, stop the GPU path here and debug the `MicroK8s` setup before moving on to pod specs or Kubeflow workloads.

## Create the Tutorial Namespace

Before creating the namespace, make sure `kubectl` points at the cluster you want to prepare:

- use `kind-kubeflow-by-doing` for the starter Kubernetes path
- use `microk8s` for the default ML path

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

If you are working on the optional GPU-capable `MicroK8s` path, apply the same namespace and quota manifests there after switching context.

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

### The `kind` starter cluster cannot request GPUs

That is expected. The `kind` starter cluster is the baseline path for the Kubernetes and Kubeflow basics.

If you want local Kubernetes GPU scheduling on WSL2, use the `MicroK8s` path from this page instead of continuing to debug `kind` node runtime wiring.

### `MicroK8s` core pods are unhealthy

Before installing Kubeflow Pipelines, make sure the cluster itself is healthy:

```bash
kubectl get pods -n kube-system
kubectl get pods -n gpu-operator-resources
```

If `kube-proxy`, `coredns`, or storage-related pods are in `CrashLoopBackOff`, do not continue to Chapter 2 yet.

## Cleanup

To delete the cluster:

```bash
kind delete cluster --name kubeflow-by-doing
```

To reset the optional GPU-ready cluster:

```bash
sudo microk8s reset
```

Do not delete it yet if you are continuing the tutorial.

## What You Learned

You created a local Kubernetes cluster and a namespace for tutorial workloads.

You also learned that local Kubernetes should be treated as disposable infrastructure.

You also saw that the tutorial separates the `kind` starter baseline from the GPU-capable `MicroK8s` path used by the later ML chapters.

## References

- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [kind configuration](https://kind.sigs.k8s.io/docs/user/configuration/)
- [Install MicroK8s on WSL2](https://microk8s.io/docs/install-wsl2)
- [MicroK8s GPU addon](https://microk8s.io/docs/addon-gpu)
- [Working with MicroK8s built-in registry](https://microk8s.io/docs/registry-built-in)
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
