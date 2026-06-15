# GPU and Node Pools

This page generalizes GPU setup across managed Kubernetes providers.

## What You Will Build

You will define a provider-neutral GPU checklist.

The pipeline stays the same:

```text
accelerator=gpu
gpu_count=1
gpu_image=<provider-registry-gpu-image>
```

The provider overlay changes:

```text
GPU node pool
node labels
driver/operator setup
quotas
cost controls
```

## Why This Matters

GPU setup is provider-specific, but the KFP requirement is stable:

```text
training pod requests nvidia.com/gpu
```

If Kubernetes exposes GPU resources, the KFP GPU path can be provider-neutral.

## Generic GPU Checklist

For any provider, verify:

```bash
kubectl get nodes -o wide
kubectl describe nodes | grep -A5 -B5 "nvidia.com/gpu" || true
```

Expected:

```text
nvidia.com/gpu: 1
```

Then run a GPU pod.

Create `infra/cloud/checks/gpu-check.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: cloud-gpu-check
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  containers:
    - name: nvidia-smi
      image: nvidia/cuda:12.6.0-base-ubuntu24.04
      command: ["nvidia-smi"]
      resources:
        limits:
          nvidia.com/gpu: 1
```

Apply:

```bash
kubectl apply -f infra/cloud/checks/gpu-check.yaml
kubectl -n kubeflow-by-doing logs pod/cloud-gpu-check
kubectl -n kubeflow-by-doing delete pod cloud-gpu-check --ignore-not-found
```

## Provider-Specific Questions

Before creating a GPU node pool, answer:

- Which GPU types are available in the region?
- Is GPU quota approved?
- Are drivers installed by the provider or by an operator?
- Does the provider require a GPU node image?
- Are GPU nodes tainted?
- Do GPU pods need tolerations?
- Can the GPU node pool scale to zero?
- What is the hourly cost?
- How will it be deleted?

## Taints and Tolerations

Many providers taint GPU nodes to prevent accidental scheduling.

If your GPU nodes are tainted, the training task may need a toleration.

Target KFP intent:

```python
from kfp import kubernetes

kubernetes.add_toleration(
    task,
    key="nvidia.com/gpu",
    operator="Exists",
    effect="NoSchedule",
)
```

Exact helper names may differ by KFP SDK version. Keep the intent the same: add a toleration to the GPU training task only when the provider taints GPU nodes.

## Node Selectors

If needed, select GPU nodes explicitly.

Target intent:

```python
from kfp import kubernetes

kubernetes.add_node_selector(
    task,
    label_key="accelerator",
    label_value="nvidia",
)
```

Do not add provider-specific selectors unless the overlay requires them.

## Pipeline Parameters

Keep the same parameters:

```text
accelerator: cpu | gpu
gpu_count: 0 | 1 | ...
gpu_image: <registry gpu image>
```

Optional provider-specific parameters:

```text
gpu_node_selector_key
gpu_node_selector_value
gpu_toleration_key
```

Only add these if needed. Do not complicate the core pipeline prematurely.

## Cost Control for GPU

GPU nodes are often the most expensive part of the tutorial.

Use:

```text
min nodes: 0 or 1
max nodes: small
short test runs
immediate cleanup
```

For learning, test with:

```text
n_train: 32
n_val: 16
epochs: 1
```

Do not run long experiments in this chapter.

## Common Problems

### GPU quota missing

The node pool cannot be created or remains unavailable.

Fix in provider quota settings before debugging Kubernetes.

### Pod pending with `Insufficient nvidia.com/gpu`

Kubernetes cannot find allocatable GPU capacity.

Check node pool, scaling, taints, and device plugin.

### Pod pending due to taints

Describe the pod and node:

```bash
kubectl describe pod -n kubeflow-by-doing cloud-gpu-check
kubectl describe node <gpu-node>
```

Look for taints and add tolerations if needed.

### GPU works with raw pod but KFP fails

Compare the raw pod spec to the KFP-created pod:

```bash
kubectl describe pod -n <namespace> <kfp-training-pod>
```

Check resource limits, tolerations, node selectors, and image.

## Acceptance Criteria

You are done when:

- GPU availability checklist exists
- raw GPU pod succeeds or CPU-only decision is documented
- KFP GPU resource request remains provider-neutral
- provider-specific taints/selectors are documented only if needed
- GPU cost control is documented before running GPU jobs

## References

- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/index.html)
- [Amazon EKS GPU workloads](https://docs.aws.amazon.com/eks/latest/userguide/ml-eks-k8s-device-plugin.html)
- [Azure AKS GPU node pools](https://learn.microsoft.com/azure/aks/gpu-cluster)
- [GKE GPUs](https://cloud.google.com/kubernetes-engine/docs/how-to/gpus)

## Next Step

Continue with [Cost and Cleanup](06-cost-and-cleanup.md).
