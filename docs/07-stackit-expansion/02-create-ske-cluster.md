# Create an SKE Cluster

This page creates or connects to a STACKIT Kubernetes Engine cluster.

## What You Will Build

You will create:

```text
infra/stackit/kubeconfig.md
```

This document records how the tutorial cluster is accessed.

## Why This Matters

The local workflow already works in Kubernetes.

The first cloud milestone is simple:

```text
kubectl can talk to SKE
```

Everything else depends on that.

## Create the Cluster

Use the STACKIT Portal first for this tutorial chapter.

Portal-first is intentional:

- it avoids hiding cloud billing choices in opaque commands
- it makes node pools visible
- it makes deletion easier to verify
- it keeps this chapter focused on Kubeflow migration

Target cluster:

```text
name: kbd-ske
purpose: tutorial / disposable
node pool: small CPU worker pool
optional later: GPU worker pool
```

Record your choices in `infra/stackit/kubeconfig.md`.

## Create `infra/stackit/kubeconfig.md`

```markdown
# STACKIT Kubeconfig

## Cluster

- Cluster name: `kbd-ske`
- Project ID: `<project-id>`
- Region: `<region>`
- Purpose: Kubeflow by Doing tutorial

## Access Method

Preferred options:

1. STACKIT Portal kubeconfig download
2. STACKIT CLI login kubeconfig

## Local Path

The tutorial expects:

```bash
export KUBECONFIG="$PWD/.kube/stackit-kubeconfig.yaml"
```

The kubeconfig file is local-only and must not be committed.

## Verification

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get namespaces
```
```

## Download Kubeconfig

Create a local folder:

```bash
mkdir -p .kube
```

Download the kubeconfig from the STACKIT Portal or STACKIT CLI and save it as:

```text
.kube/stackit-kubeconfig.yaml
```

Then run:

```bash
export KUBECONFIG="$PWD/.kube/stackit-kubeconfig.yaml"
kubectl cluster-info
kubectl get nodes -o wide
```

## STACKIT CLI Access Pattern

If using the STACKIT CLI, the general flow is:

```bash
stackit auth login
stackit config set --project-id "$STACKIT_PROJECT_ID"
stackit ske kubeconfig create "$STACKIT_CLUSTER_NAME" --login > .kube/stackit-kubeconfig.yaml
export KUBECONFIG="$PWD/.kube/stackit-kubeconfig.yaml"
```

!!! note

    Check the current STACKIT CLI help if the exact command differs:

    ```bash
    stackit ske kubeconfig create --help
    ```

## Create Tutorial Namespace

```bash
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
```

Verify:

```bash
kubectl get namespace kubeflow-by-doing
```

## Check Storage Classes

```bash
kubectl get storageclass
```

You will need a default storage class for components such as KFP, MLflow, or any PVC-backed service.

## Check LoadBalancer Support

The core tutorial still uses port-forwarding first.

But it is useful to know whether `Service` type `LoadBalancer` is supported:

```bash
kubectl get svc -A
```

Do not expose services publicly yet.

## Common Problems

### `kubectl` points to the wrong cluster

Check:

```bash
kubectl config current-context
kubectl config get-contexts
```

Set:

```bash
export KUBECONFIG="$PWD/.kube/stackit-kubeconfig.yaml"
```

### Missing permissions

Make sure your STACKIT user has permission to access the SKE cluster and project.

### Cluster exists but nodes are not ready

Inspect:

```bash
kubectl get nodes
kubectl describe nodes
kubectl get pods -A
```

If the issue is cloud-side, use the STACKIT Portal and support documentation.

## Acceptance Criteria

You are done when:

- SKE cluster exists
- kubeconfig is saved locally under `.kube/`
- `kubectl cluster-info` works
- `kubectl get nodes` shows ready nodes
- namespace `kubeflow-by-doing` exists
- you know how to delete the cluster later

## References

- [Create a STACKIT Kubernetes Engine cluster](https://docs.stackit.cloud/products/runtime/kubernetes-engine/getting-started/create-cluster/)
- [Access an SKE cluster](https://docs.stackit.cloud/products/runtime/kubernetes-engine/getting-started/access-cluster/)
- [STACKIT CLI developer tools](https://docs.stackit.cloud/developer-tools/)

## Next Step

Continue with [Container Registry and Images](03-container-registry-and-images.md).
