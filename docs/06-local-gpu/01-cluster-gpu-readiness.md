# Cluster GPU Readiness

This page verifies that the current local cluster is ready for GPU-aware Kubeflow runs.

It does not re-teach GPU setup. It only checks the assumptions needed by the rest of Chapter 6.

## What You Will Check

You will verify:

- which cluster context is active
- whether the cluster is MicroK8s or kind
- whether nodes advertise `nvidia.com/gpu`
- whether a small GPU pod can run
- what to do if the GPU path is unavailable

## Preferred Path: MicroK8s

For GPU-capable local Kubeflow work, MicroK8s is the preferred local platform in this tutorial.

Check the current context:

```bash
kubectl config current-context
```

If you use MicroK8s directly:

```bash
microk8s status
microk8s kubectl get nodes
```

## Verify GPU Capacity

```bash
kubectl describe nodes | grep -A5 -B5 "nvidia.com/gpu" || true
```

Expected shape:

```text
Capacity:
  nvidia.com/gpu: 1
Allocatable:
  nvidia.com/gpu: 1
```

If this does not appear, Kubernetes does not currently expose the GPU as a schedulable resource.

## Optional Pod Check

If you want a pod-level confirmation, reuse the Chapter 1 GPU smoke test manifest:

```bash
kubectl apply -f infra/k8s/gpu-smoke-test.yaml
kubectl -n kubeflow-by-doing get pod gpu-smoke-test -w
```

Inspect logs:

```bash
kubectl -n kubeflow-by-doing logs pod/gpu-smoke-test
```

Clean up:

```bash
kubectl -n kubeflow-by-doing delete pod gpu-smoke-test --ignore-not-found
```

## kind Fallback

If you are using `kind`, the CPU path remains valid.

For this chapter:

```text
MicroK8s GPU path = expected GPU integration path
kind fallback     = CPU-only validation path unless you have explicitly configured GPU support
```

The rest of the chapter keeps the CPU fallback path available.

## Common Problems

### `nvidia.com/gpu` does not appear on the node

The KFP GPU step will not schedule.

Check:

```bash
kubectl get nodes
kubectl describe nodes
kubectl get pods -A | grep -i nvidia || true
```

If you have not completed the GPU-capable MicroK8s bootstrap yet, return to Chapter 1 and finish the cluster setup there before continuing this chapter.

### GPU pod stays `Pending`

Describe it:

```bash
kubectl -n kubeflow-by-doing describe pod gpu-smoke-pod
```

Look for:

```text
Insufficient nvidia.com/gpu
```

## Acceptance Criteria

You are done when:

- you know whether your active cluster is MicroK8s or kind
- MicroK8s nodes advertise `nvidia.com/gpu`, or you explicitly choose the CPU fallback path
- the GPU smoke pod succeeds on GPU-capable MicroK8s
- you can identify `Insufficient nvidia.com/gpu` in pod events
- if the GPU path is unavailable, you know to stop and revisit the cluster bootstrap instead of debugging KFP first

## References

- [MicroK8s GPU add-on](https://canonical.com/microk8s/docs/addon-gpu)
- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [Kubernetes device plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/)

## Next Step

Continue with [GPU Training Image](02-gpu-training-image.md).
