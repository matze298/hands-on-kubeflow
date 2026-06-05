# Install Kubeflow Pipelines

This page installs standalone Kubeflow Pipelines into the local Kubernetes cluster created in Chapter 1.

From this chapter onward, the tutorial assumes you use the GPU-capable local cluster path. If you need to switch from the default `kind` cluster to the `minikube` GPU profile, go back to [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md) and follow the "Optional: Create a GPU-Capable Local Cluster" and "Create the Tutorial Namespace" sections before continuing.

We install Kubeflow Pipelines only, not the full Kubeflow platform.

## What You Will Build

You will install KFP into a namespace called:

```text
kubeflow
```

You will then access the KFP UI locally through port forwarding.

## Why This Matters

Kubeflow Pipelines is enough to learn the core workflow:

```text
component → pipeline → run → logs → metrics → artifacts
```

Installing the full Kubeflow platform too early adds authentication, multi-user namespaces, notebooks, dashboards, and more infrastructure complexity before the workflow itself is clear.

## Prerequisites

You should have completed Chapter 1.

Verify that your local cluster is running:

```bash
kubectl get nodes
```

Expected:

```text
STATUS   Ready
```

Verify your current context:

```bash
kubectl config current-context
```

Expected:

```text
kubeflow-by-doing-gpu
```

That is the GPU-capable `minikube` profile created in Chapter 1.

If you still see `kind-kubeflow-by-doing`, switch now:

```bash
kubectl config use-context kubeflow-by-doing-gpu
kubectl config set-context --current --namespace=kubeflow-by-doing
```

If either command fails, return to [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md) and complete the GPU-cluster and namespace setup there first.

## Choose a KFP Version

Pin the version instead of installing from a moving branch.

Create an environment variable:

```bash
export KFP_VERSION=2.14.3
```

!!! note

    If this exact version is no longer current when you read this, check the Kubeflow Pipelines release page and update `KFP_VERSION` intentionally. Do not install from an unpinned branch in a tutorial repo.

## Install KFP Manifests

Create the namespace:

```bash
kubectl create namespace kubeflow --dry-run=client -o yaml | kubectl apply -f -
```

Apply the cluster-scoped resources:

```bash
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=${KFP_VERSION}"
```

Wait briefly for custom resource definitions to register:

```bash
kubectl wait --for condition=established --timeout=120s crd/applications.app.k8s.io
```

Apply the platform-agnostic deployment:

```bash
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic?ref=${KFP_VERSION}"
```

!!! warning

    KFP installation manifests can change between releases. If these commands fail, keep the chapter structure but follow the current official KFP installation guide and pin the version that works for the tutorial.

## Wait for KFP Pods

Watch the `kubeflow` namespace:

```bash
kubectl get pods -n kubeflow -w
```

You are looking for most pods to become `Running` or `Completed`.

You can also run:

```bash
kubectl get pods -n kubeflow
```

Useful filter:

```bash
kubectl get pods -n kubeflow | grep -E "ml-pipeline|metadata|minio|mysql|workflow|viewer|cache"
```

## Access the UI

Port-forward the KFP UI:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

Open:

```text
http://localhost:8080
```

You should see the Kubeflow Pipelines UI.

## Verify KFP Services

In a second terminal:

```bash
kubectl get svc -n kubeflow
```

Look for services such as:

```text
ml-pipeline
ml-pipeline-ui
metadata-grpc-service
minio-service
mysql
```

Exact names can differ by KFP release.

## Set Up the Python SDK

Add the KFP SDK to your tutorial project:

```bash
uv add kfp
```

Verify:

```bash
uv run python - <<'PY'
import kfp
print(kfp.__version__)
PY
```

## Verify the Result

At this point, the earlier checks should already have shown that:

- `kubectl get pods -n kubeflow` reports KFP pods in `Running` or `Completed`
- `kubectl get svc -n kubeflow` includes `ml-pipeline-ui`
- `http://localhost:8080` opens the KFP UI through port forwarding
- `uv run python -c "import kfp; print(kfp.__version__)"` works locally

If one of those checks still fails, use the matching troubleshooting section below before moving on.

## Common Problems

### `kubectl apply -k ...` fails with a GitHub or Kustomize error

Common causes:

- wrong `KFP_VERSION`
- incompatible `kustomize` version
- temporary GitHub/network issue
- KFP manifest path changed

Check the official installation docs and pin a known-good version in the tutorial.

### Pods stay `Pending`

Check resources:

```bash
kubectl describe pod -n kubeflow <pod-name>
kubectl get events -n kubeflow --sort-by=.lastTimestamp
```

Your local Docker or WSL2 environment may not have enough CPU or memory.

### Pods are `ImagePullBackOff`

Inspect the failed pod:

```bash
kubectl describe pod -n kubeflow <pod-name>
```

Common causes:

- registry access issue
- image name changed
- network problem
- version mismatch

### UI is not reachable

Check that the service exists:

```bash
kubectl get svc -n kubeflow ml-pipeline-ui
```

Restart port forwarding:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

Then open:

```text
http://localhost:8080
```

### Port 8080 is already in use

Use another local port:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 18080:80
```

Open:

```text
http://localhost:18080
```

## Cleanup

Do not clean up if you are continuing the chapter.

To remove KFP later:

```bash
kubectl delete -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic?ref=${KFP_VERSION}"
kubectl delete -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=${KFP_VERSION}"
```

If the local cluster is disposable, the simpler cleanup is to delete the cluster backend you used in Chapter 1.

```bash
minikube delete --profile kubeflow-by-doing-gpu
```

If you intentionally stayed on the CPU-only baseline instead, use:

```bash
kind delete cluster --name kubeflow-by-doing
```

## What You Learned

You installed standalone Kubeflow Pipelines locally and opened the KFP UI.

The important distinction is:

```text
Kubernetes runs workloads.
Kubeflow Pipelines defines, tracks, and orchestrates ML workflows on top of Kubernetes.
```

## References

- [Kubeflow Pipelines installation](https://www.kubeflow.org/docs/components/pipelines/operator-guides/installation/)
- [Kubeflow Pipelines local deployment](https://www.kubeflow.org/docs/components/pipelines/legacy-v1/installation/localcluster-deployment/)
- [Kubeflow Pipelines GitHub repository](https://github.com/kubeflow/pipelines)

## Acceptance Criteria

You are done when:

- `kubectl get pods -n kubeflow` shows KFP pods running
- `kubectl get svc -n kubeflow` shows `ml-pipeline-ui`
- the KFP UI opens in your browser through port forwarding
- `uv run python -c "import kfp; print(kfp.__version__)"` works

## Next Step

Continue with [First Pipeline](02-first-pipeline.md).
