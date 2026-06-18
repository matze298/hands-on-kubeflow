# FAQ

This page collects recovery procedures that are useful when a local tutorial environment gets into a confusing state.

Use the smallest reset that solves the problem. A namespace reset is usually enough for a broken tutorial service. A full `k3s` reset is a local-cluster rebuild.

For a compact map of what the tutorial creates, see the [Local Platform Inventory](../reference/local-platform-inventory.md). For version pins and upgrade checks, see [Version Compatibility](../reference/version-compatibility.md).

## Prerequisites

Before using a reset procedure, make sure:

- you know which chapter you want to resume
- you know whether that chapter expects the `k3s-kubeflow` context, the `kind` fallback, or a cloud cluster
- you have checked the relevant chapter overview for its restart prerequisites
- you are not pointing `kubectl` at a shared or production cluster

## How Do I Reset `k3s`?

Start by confirming that you are looking at the tutorial cluster:

```bash
kubectl config current-context
kubectl get nodes
kubectl get namespaces
```

For the default local ML path, the current context should be:

```text
k3s-kubeflow
```

If you are still setting up the cluster, return to [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md), especially the `k3s` bootstrap and namespace sections.

### `kubectl` Says the Server Refused the Connection

This error means `kubectl` is using a kubeconfig entry for a local API server port, but the `k3s` control plane behind that port is not running:

```text
Get "https://127.0.0.1:32771/api?timeout=32s": dial tcp 127.0.0.1:32771: connect: connection refused
The connection to the server 127.0.0.1:32771 was refused - did you specify the right host or port?
```

First confirm that `kubectl` is pointing at the tutorial context and check the `k3s` service:

```bash
kubectl config current-context
sudo systemctl status k3s --no-pager
```

If the context is `k3s-kubeflow` but the service is stopped or the API server refuses connections, restart the tutorial cluster setup:

```bash
bash infra/k3s/deploy_cluster.sh
```

If the service still fails early with `too many open files` or inotify errors, return to [Install the Local Toolchain](../01-local-kubernetes/01-install-toolchain.md) and reapply the inotify setup before starting k3s again:

```bash
sudo sysctl -w fs.inotify.max_user_instances=1024
sudo sysctl -w fs.inotify.max_user_watches=1048576
sudo systemctl restart k3s
```

After the profile starts, restore the tutorial namespace on the current context:

```bash
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
kubectl config set-context --current --namespace=kubeflow-by-doing
```

Then check that the API server and GPU device plugin are visible:

```bash
kubectl get pods
kubectl get pods -n kube-system
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity gpu="}{.status.capacity.nvidia\.com/gpu}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

### Soft Reset Tutorial Workloads

Use this when Kubernetes itself is healthy but the tutorial workloads are stale, partially installed, or no longer match the chapter you are following.

```bash
kubectl config use-context k3s-kubeflow
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

### Hard Reset the `k3s` Cluster

Use this when core cluster pods are unhealthy, GPU addon state is broken, storage is inconsistent, or you want a clean local cluster.

!!! warning

    This deletes workloads and cluster state from the local `k3s` cluster. Do not run it against a shared or non-tutorial cluster.

Stop local port forwards first, then run:

```bash
sudo k3s-uninstall.sh
```

Rebuild the tutorial cluster setup from Chapter 1:

```bash
curl -sfL https://get.k3s.io | sudo env INSTALL_K3S_EXEC="--docker --write-kubeconfig-mode 644" sh -
bash infra/k3s/deploy_cluster.sh
```

`deploy_cluster.sh` refreshes the user kubeconfig after every k3s reinstall and merges the `k3s-kubeflow` context into the normal `~/.kube/config`. If you need to do that step manually, export the k3s kubeconfig into a temporary file and merge it before using `kubectl`:

```bash
mkdir -p ~/.kube
source_kubeconfig="$(mktemp)"
merged_kubeconfig="$(mktemp)"
sudo k3s kubectl config view --raw --flatten > "${source_kubeconfig}"
sed -i \
  -e "s/name: default/name: k3s-kubeflow/g" \
  -e "s/cluster: default/cluster: k3s-kubeflow/g" \
  -e "s/user: default/user: k3s-kubeflow/g" \
  -e "s/current-context: default/current-context: k3s-kubeflow/g" \
  "${source_kubeconfig}"
if [ -f "$HOME/.kube/config" ]; then
  export KUBECONFIG="${source_kubeconfig}:$HOME/.kube/config"
else
  export KUBECONFIG="${source_kubeconfig}"
fi
kubectl config view --flatten > "${merged_kubeconfig}"
mv "${merged_kubeconfig}" ~/.kube/config
chmod 600 ~/.kube/config
export KUBECONFIG="$HOME/.kube/config"
kubectl config use-context k3s-kubeflow
kubectl config set-context --current --namespace=kubeflow-by-doing
rm -f "${source_kubeconfig}"
```

Verify the cluster before reinstalling Kubeflow components:

```bash
kubectl get nodes -o wide
kubectl get pods -n kube-system
kubectl get pods -A | grep -i nvidia || true
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" capacity gpu="}{.status.capacity.nvidia\.com/gpu}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
```

If GPU allocatable is empty, stay in Chapter 1 and fix the `k3s` GPU path before continuing to Kubeflow Pipelines.

## Which k3s GPU Setup Error Did I Hit?

These are the local WSL2/k3s failure modes this tutorial path is designed around.

| Symptom | What it usually means | Fix |
|---|---|---|
| `inotify_init: too many open files` or `Failed to start cAdvisor` | WSL/Linux inotify limits are too low for local Kubernetes. | Reapply the inotify `sysctl` commands from the toolchain page, then restart k3s. |
| `failed to load flannel 'subnet.env'` | k3s networking is not fully initialized yet. | Wait for `kube-system` and `/run/flannel/subnet.env`; `deploy_cluster.sh` waits for this before continuing. |
| NVIDIA device plugin logs `Failed to initialize NVML: ERROR_LIBRARY_NOT_FOUND` | Docker can see the GPU, but Kubernetes pods are not getting the NVIDIA runtime. | Reapply the Docker NVIDIA default-runtime commands from the toolchain page, then restart Docker and k3s. |
| Node shows no `nvidia.com/gpu`, but the device plugin pod is running | Device-plugin registration may still be settling, or the plugin cannot see NVML. | Check `kubectl logs -n kube-system -l name=nvidia-device-plugin-ds --tail=120` and `kubectl describe node ...`; rerun `deploy_cluster.sh` if it never registers. |
| GPU pod event says `RuntimeHandler "nvidia" not supported` | The Docker-backed k3s path is not using a Kubernetes `RuntimeClass` handler. | Omit `runtimeClassName`; rely on Docker's default NVIDIA runtime. |
| Kubeflow storage pods stay `Pending` with unbound PVCs on the old local setup | The previous local cluster path could fail before Kubeflow had working storage. | Use the k3s path and verify the default `local-path` storage class before installing KFP. |

For the detailed commands and expected outputs, return to [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md) and [GPU Smoke Test](../01-local-kubernetes/05-gpu-smoke-test.md).

## How Do I Reset Kubeflow?

In this tutorial, "Kubeflow" usually means standalone Kubeflow Pipelines installed in the `kubeflow` namespace, not the full Kubeflow platform.

Start with inspection:

```bash
kubectl config current-context
kubectl get pods -n kubeflow
kubectl get events -n kubeflow --sort-by=.lastTimestamp
```

If the current context is not `k3s-kubeflow`, switch back before resetting local KFP:

```bash
kubectl config use-context k3s-kubeflow
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
| `kube-system` pods are broken | hard reset `k3s` |
| GPU resources disappeared | verify Chapter 1 GPU setup, then hard reset `k3s` if needed |

## Acceptance Criteria

You are done when:

- `kubectl config current-context` is `k3s-kubeflow`
- `kubectl get nodes` shows ready nodes
- `kubectl get pods -n kube-system` has no unexpected `CrashLoopBackOff` pods
- `kubectl get namespace kubeflow-by-doing` succeeds
- if you reinstalled KFP, `kubectl get pods -n kubeflow` shows the core KFP pods running or completed
- if you use GPU chapters, the node reports non-empty `nvidia.com/gpu` allocatable capacity
