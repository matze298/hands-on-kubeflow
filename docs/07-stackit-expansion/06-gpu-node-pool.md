# GPU Node Pool

This page adds optional GPU validation on STACKIT.

## What You Will Build

You will create:

```text
infra/stackit/gpu-check.yaml
```

You will then run:

```text
nvidia.com/gpu scheduling check
optional GPU KFP run
```

## Why This Matters

A cloud cluster is not GPU-ready just because it is managed.

You still need:

- GPU-capable node pool
- NVIDIA GPU support on nodes
- Kubernetes advertises `nvidia.com/gpu`
- training image supports CUDA
- KFP task requests the GPU

## Create or Add a GPU Node Pool

Use the STACKIT Portal or CLI according to your project permissions.

Target:

```text
cluster: kbd-ske
node pool: gpu-pool
GPU worker type: project-approved GPU flavor
min nodes: 0 or 1 depending on autoscaling/cost setup
max nodes: small number for tutorial
```

!!! warning

    GPU resources can be expensive. Keep the node pool small, delete it after the exercise, and verify billing assumptions before running long jobs.

## Check Nodes

```bash
kubectl get nodes -o wide
kubectl describe nodes | grep -A5 -B5 "nvidia.com/gpu" || true
```

Expected shape:

```text
nvidia.com/gpu: 1
```

If the GPU is not advertised, follow the current STACKIT GPU workload guide for SKE.

## Create `infra/stackit/gpu-check.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: stackit-gpu-check
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
kubectl apply -f infra/stackit/gpu-check.yaml
kubectl -n kubeflow-by-doing get pod stackit-gpu-check -w
kubectl -n kubeflow-by-doing logs pod/stackit-gpu-check
```

Cleanup:

```bash
kubectl -n kubeflow-by-doing delete pod stackit-gpu-check --ignore-not-found
```

## Push or Select a GPU Training Image

If you built a GPU image in Chapter 6, push it to the registry:

```bash
export KBD_GPU_TRAIN_IMAGE="$KBD_REGISTRY_HOST/$KBD_REGISTRY_NAMESPACE/kubeflow-by-doing-train:gpu-stackit"

docker build -f Dockerfile.gpu -t "$KBD_GPU_TRAIN_IMAGE" .
docker push "$KBD_GPU_TRAIN_IMAGE"
```

## Run GPU KFP Path

Run the pipeline with:

```text
run_id: stackit-gpu-001
accelerator: gpu
gpu_count: 1
cpu_image: <KBD_TRAIN_IMAGE>
gpu_image: <KBD_GPU_TRAIN_IMAGE>
min_accuracy: 0.5
```

## Verify GPU Scheduling

Find the training pod:

```bash
kubectl get pods -A --sort-by=.metadata.creationTimestamp
```

Describe it:

```bash
kubectl describe pod -n <namespace> <training-pod>
```

Look for:

```text
Limits:
  nvidia.com/gpu: 1
```

Check logs:

```bash
kubectl logs -n <namespace> <training-pod>
```

Look for:

```text
device: cuda
```

or CUDA availability output.

## Common Problems

### GPU pod stays Pending

Look for:

```text
Insufficient nvidia.com/gpu
```

Likely causes:

- no GPU node pool
- GPU node pool scaled to zero and autoscaler not provisioning
- wrong resource request
- quota or project limit
- GPU add-on/driver setup incomplete

### Image works locally but not on SKE

SKE cannot use local Docker images.

Push the image to a registry and update `gpu_image`.

### GPU node pool costs too much

Scale to zero or delete the GPU node pool after validation.

## Acceptance Criteria

You are done when:

- GPU node pool exists or CPU-only decision is documented
- `nvidia.com/gpu` appears on SKE nodes
- `stackit-gpu-check` succeeds
- GPU training image is available from registry
- GPU KFP run succeeds or failure is clearly explained
- GPU resources are cleaned up or scaled down after the exercise

## References

- [Use NVIDIA GPUs with SKE](https://docs.stackit.cloud/products/runtime/kubernetes-engine/how-tos/use-nvidia-gpus/)
- [Manage SKE node pools](https://docs.stackit.cloud/products/runtime/kubernetes-engine/getting-started/node-pools/)
- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/index.html)

## Next Step

Continue with [Cost Control and Cleanup](07-cost-control-and-cleanup.md).
