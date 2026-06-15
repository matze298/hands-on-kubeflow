# FAQ

This page collects recovery procedures that are useful when a local tutorial environment gets into a confusing state.

Use the smallest reset that solves the problem. A namespace reset is usually enough for a broken tutorial service. A full `minikube` reset is a local-cluster rebuild.

For a compact map of what the tutorial creates, see the [Local Platform Inventory](../reference/local-platform-inventory.md). For version pins and upgrade checks, see [Version Compatibility](../reference/version-compatibility.md).

## How Do I Reset `minikube`?

Start by confirming that you are looking at the tutorial cluster:

```bash
kubectl config current-context
kubectl get nodes
kubectl get namespaces
```

For the default local ML path, the current context should be:

```text
kubeflow-gpu
```

If you are still setting up the cluster, return to [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md), especially the `minikube` bootstrap and namespace sections.

### Soft Reset Tutorial Workloads

Use this when Kubernetes itself is healthy but the tutorial workloads are stale, partially installed, or no longer match the chapter you are following.

```bash
kubectl config use-context kubeflow-gpu
kubectl delete namespace kubeflow-by-doing --ignore-not-found
kubectl delete namespace kubeflow --ignore-not-found
kubectl delete namespace minio --ignore-not-found
```

Then recreate the tutorial namespace:

```bash
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace=kubeflow-by-doing
```

After this reset, reinstall only the pieces needed by your current chapter:

- [Install Kubeflow Pipelines](../02-kubeflow-pipelines/01-install-kfp.md)
- [Install Local Object Storage](../04-artifacts-and-tracking/01-install-minio.md)
- [Add Experiment Tracking](../04-artifacts-and-tracking/03-add-mlflow.md)

### Hard Reset the `minikube` Cluster

Use this when core cluster pods are unhealthy, GPU addon state is broken, storage is inconsistent, or you want a clean local cluster.

!!! warning

    This deletes workloads and cluster state from the local `minikube` cluster. Do not run it against a shared or non-tutorial cluster.

Stop local port forwards first, then run:

```bash
minikube delete -p kubeflow-gpu
```

Rebuild the tutorial cluster setup from Chapter 1:

```bash
bash infra/minikube/bootstrap-gpu-cluster.sh
```

Verify the cluster before reinstalling Kubeflow components:

```bash
kubectl get nodes -o wide
kubectl get pods -n kube-system
kubectl get pods -A | grep -i nvidia || true
minikube addons list -p kubeflow-gpu | grep -i nvidia
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity gpu="}{.status.capacity.nvidia\.com/gpu}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

If GPU allocatable is empty, stay in Chapter 1 and fix the `minikube` GPU path before continuing to Kubeflow Pipelines.

## How Do I Reset Kubeflow?

In this tutorial, "Kubeflow" usually means standalone Kubeflow Pipelines installed in the `kubeflow` namespace, not the full Kubeflow platform.

Start with inspection:

```bash
kubectl config current-context
kubectl get pods -n kubeflow
kubectl get events -n kubeflow --sort-by=.lastTimestamp
```

If the current context is not `kubeflow-gpu`, switch back before resetting local KFP:

```bash
kubectl config use-context kubeflow-gpu
```

### Restart KFP Pods

Use this when the KFP install is mostly healthy but a pod is stuck, a port-forward stopped working, or you changed local cluster resources.

```bash
kubectl -n kubeflow delete pod --all
kubectl get pods -n kubeflow -w
```

The deployments and services remain; Kubernetes recreates the pods.

### Reinstall Standalone Kubeflow Pipelines

Use this when the KFP namespace contains a failed or incompatible install.

```bash
export KFP_VERSION=2.16.1

kubectl delete -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=${KFP_VERSION}" --ignore-not-found
kubectl delete -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=${KFP_VERSION}" --ignore-not-found
kubectl delete namespace kubeflow --ignore-not-found
```

Wait until the namespace is gone:

```bash
kubectl get namespace kubeflow
```

If it still appears as `Terminating`, inspect finalizers before deleting anything else:

```bash
kubectl get namespace kubeflow -o yaml
```

Then reinstall from [Install Kubeflow Pipelines](../02-kubeflow-pipelines/01-install-kfp.md).

### Reset Tutorial Data Around KFP

KFP is not the only stateful part of the local workflow. If a pipeline run still points at old artifacts or services, also consider whether you need to reset:

- MinIO from [Install Local Object Storage](../04-artifacts-and-tracking/01-install-minio.md)
- MLflow from [Add Experiment Tracking](../04-artifacts-and-tracking/03-add-mlflow.md)
- local images from [Containerize Training](../03-local-ml-workflow/05-containerize-training.md)

Do not delete object storage just to fix the KFP UI. Delete MinIO only when you are comfortable losing local tutorial artifacts.

## Which Reset Should I Use?

| Symptom | First reset to try |
|---|---|
| KFP UI port-forward stopped | restart the port-forward, then restart KFP pods |
| A few KFP pods are stale or stuck | restart KFP pods |
| KFP manifest install failed halfway | reinstall standalone KFP |
| `kubeflow-by-doing` workloads are stale | soft reset tutorial workloads |
| MinIO or MLflow data is wrong | reset that chapter's namespace or manifests deliberately |
| `kube-system` pods are broken | hard reset `minikube` |
| GPU resources disappeared | verify Chapter 1 GPU setup, then hard reset `minikube` if needed |

## Acceptance Criteria

You are done when:

- `kubectl config current-context` is `kubeflow-gpu`
- `kubectl get nodes` shows ready nodes
- `kubectl get pods -n kube-system` has no unexpected `CrashLoopBackOff` pods
- `kubectl get namespace kubeflow-by-doing` succeeds
- if you reinstalled KFP, `kubectl get pods -n kubeflow` shows the core KFP pods running or completed
- if you use GPU chapters, the node reports non-empty `nvidia.com/gpu` allocatable capacity
