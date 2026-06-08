# Provider Checklist

This page provides the final checklist for adapting the tutorial to any managed Kubernetes provider.

## 1. Kubernetes Access

```bash
export KUBECONFIG="$PWD/.kube/<provider>-kubeconfig.yaml"
kubectl cluster-info
kubectl get nodes -o wide
kubectl create namespace kubeflow-by-doing --dry-run=client -o yaml | kubectl apply -f -
```

Done when:

```text
kubectl can access the cluster
nodes are Ready
tutorial namespace exists
```

## 2. Storage Classes

```bash
kubectl get storageclass
```

Done when:

```text
KFP and MLflow can create or use needed storage
```

## 3. Registry Access

```bash
kubectl apply -f infra/cloud/checks/image-pull-check.generated.yaml
kubectl -n kubeflow-by-doing logs pod/image-pull-check
```

Done when:

```text
managed Kubernetes can pull tutorial images
```

## 4. Object Storage Access

```bash
source .env.cloud
uv run python infra/cloud/checks/object-storage-check.py

kubectl apply -f infra/cloud/checks/object-storage-pod-check.yaml
kubectl -n kubeflow-by-doing logs pod/object-storage-pod-check
```

Done when:

```text
laptop and pods can access the artifact bucket
```

## 5. KFP Installation

```bash
kubectl get pods -n kubeflow
kubectl -n kubeflow port-forward svc/ml-pipeline-ui 8080:80
```

Done when:

```text
KFP UI opens
KFP API is reachable
```

## 6. Pipeline Parameters

Use provider overlay values:

```text
cpu_image
gpu_image
artifact bucket
pipeline root
run_id
accelerator
gpu_count
```

Done when:

```text
pipeline code does not change
only parameters and secrets change
```

## 7. CPU Run

Run:

```text
accelerator=cpu
gpu_count=0
```

Done when:

```text
train/evaluate/promote/lineage run succeeds
artifacts are written
```

## 8. GPU Run

Run only if GPU node pool is available:

```text
accelerator=gpu
gpu_count=1
```

Done when:

```text
training pod requests nvidia.com/gpu
training logs show CUDA
```

If not available, document:

```text
CPU-only provider run
GPU not configured
```

## 9. Serving

Start private:

```bash
kubectl -n kubeflow-by-doing port-forward svc/model-server 8000:8000
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

Done when:

```text
private endpoint works through port-forwarding
```

Do not add public ingress until the private path works.

## 10. Cleanup Plan

Before creating expensive resources, fill:

```text
cluster:
node pools:
GPU node pool:
bucket:
registry:
cleanup owner:
cleanup date:
```

Done when:

```text
you know how to delete everything you created
```

## Provider-Neutral Success Definition

A provider expansion is successful when:

```text
same pipeline code
different provider overlay
same artifact layout
same debugging workflow
explicit cleanup
```

## What to Commit

Commit:

```text
infra/cloud/*.md
infra/cloud/*.template.yaml
infra/cloud/checks/*.yaml
infra/cloud/checks/*.py
infra/cloud/cleanup/*.md
docs/
```

Do not commit:

```text
.env.cloud
.kube/
*.generated.yaml with real secrets
provider credentials
```

## Final Acceptance Criteria

You are done with Chapter 8 when:

- you can identify provider-specific configuration
- you can keep pipeline code provider-neutral
- you can plan cleanup for cloud resources
- you have provider overlays for at least one target cloud
- CPU run is validated or planned
- GPU run is validated or explicitly deferred
- secrets and credentials are not committed

## References

- [Kubeflow Pipelines documentation](https://www.kubeflow.org/docs/components/pipelines/)
- [Kubernetes private registry pulls](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)
- [Kubernetes kubeconfig documentation](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)

## Next Step

Continue with Chapter 9: CI/CD and Automation.
