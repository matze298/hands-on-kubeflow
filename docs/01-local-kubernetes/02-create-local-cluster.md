# Create a Local Kubernetes Cluster

In this page, you create the local Kubernetes cluster used for the rest of the tutorial.

We use `kind` as the default cluster backend.

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

## Create the Tutorial Namespace

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

## Cleanup

To delete the cluster:

```bash
kind delete cluster --name kubeflow-by-doing
```

Do not delete it yet if you are continuing the tutorial.

## What You Learned

You created a local Kubernetes cluster and a namespace for tutorial workloads.

You also learned that local Kubernetes should be treated as disposable infrastructure.

## References

- [kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
- [kind configuration](https://kind.sigs.k8s.io/docs/user/configuration/)
- [Kubernetes namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
- [Kubernetes resource quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)

## Acceptance Criteria

You are done when:

- `kubectl get nodes` shows ready nodes
- `kubectl config view --minify` points to `kind-kubeflow-by-doing`
- the default namespace is `kubeflow-by-doing`
- `kubectl get pods -A` works
- you know how to delete and recreate the cluster

## Next Step

Continue with [First Kubernetes Job](03-first-kubernetes-job.md).
