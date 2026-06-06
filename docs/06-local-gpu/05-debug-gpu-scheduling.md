# Debug GPU Scheduling

This page shows how GPU failures appear in KFP and Kubernetes.

## What You Will Debug

You will learn how to distinguish:

```text
image problem
CUDA problem
Kubernetes scheduling problem
KFP configuration problem
```

## Failure Type 1: Pod Pending

Symptom:

```text
KFP step does not start
pod is Pending
```

Inspect pods:

```bash
kubectl get pods -A --sort-by=.metadata.creationTimestamp
kubectl describe pod -n <namespace> <training-pod>
```

Look for:

```text
Insufficient nvidia.com/gpu
```

Meaning:

```text
KFP requested a GPU, but Kubernetes cannot find an allocatable GPU.
```

Fix:

- use MicroK8s GPU path
- enable GPU add-on
- check node capacity
- reduce `gpu_count`
- switch to CPU fallback

## Failure Type 2: Image Pull Failure

Symptom:

```text
ImagePullBackOff
ErrImagePull
```

Inspect:

```bash
kubectl describe pod -n <namespace> <training-pod>
```

Meaning:

```text
Kubernetes cannot access the GPU training image.
```

Fix for MicroK8s:

```bash
docker save kubeflow-by-doing/train:gpu-local | sudo microk8s ctr image import -
```

On `kind`, this failure is expected in the default tutorial flow because the GPU path is not the supported path there. Switch to the CPU fallback run or move to the MicroK8s GPU path before debugging the GPU image itself.

If you have separately configured a GPU-capable `kind` environment, you can still fix the image load the same way as the CPU image path, then rerun the GPU job.

## Failure Type 3: CUDA Unavailable

Symptom:

```text
RuntimeError: CUDA was requested, but torch.cuda.is_available() is false
```

Meaning:

```text
The pod started, but PyTorch cannot see CUDA.
```

Check:

```bash
kubectl logs -n <namespace> <training-pod>
kubectl describe pod -n <namespace> <training-pod>
```

Likely causes:

- GPU resource was not requested
- wrong image
- node runtime does not expose GPU devices
- CUDA/PyTorch image mismatch

## Failure Type 4: Wrong Accelerator Branch

Symptom:

```text
accelerator=gpu run uses CPU image
```

or:

```text
accelerator=cpu run requests GPU
```

Meaning:

```text
Pipeline parameter wiring is wrong.
```

Check compiled pipeline:

```bash
grep -n "kubeflow-by-doing/train\\|nvidia.com/gpu\\|accelerator" compiled/image_classification_pipeline.yaml || true
```

Then inspect the actual pod:

```bash
kubectl describe pod -n <namespace> <training-pod>
```

## KFP UI Debugging Flow

In the KFP UI:

1. open the failed or pending run
2. identify the training step
3. open logs if available
4. note whether the step created a pod
5. switch to `kubectl` for pod details

Then run:

```bash
kubectl get pods -A --sort-by=.metadata.creationTimestamp
kubectl get events -A --sort-by=.lastTimestamp
```

## Intentional Failure Exercise

Run the GPU path with:

```text
gpu_count: 99
```

Expected:

```text
training pod stays Pending
```

Find the event:

```text
Insufficient nvidia.com/gpu
```

Then rerun with:

```text
gpu_count: 1
```

or switch to:

```text
accelerator: cpu
```

## What Good Looks Like

A good GPU-integrated KFP run has:

```text
KFP run succeeds
training pod requested nvidia.com/gpu
training logs show device=cuda
artifacts are written
CPU fallback still works
```

## Acceptance Criteria

You are done when:

- you can identify a pending GPU pod
- you can find `Insufficient nvidia.com/gpu`
- you can distinguish image pull errors from CUDA runtime errors
- you can confirm whether the training pod requested GPU resources
- you can recover by switching to CPU fallback
- you can explain why `nvidia-smi` working locally is not the same as KFP GPU integration

## References

- [Kubernetes GPU scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)
- [Kubernetes events](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
- [Kubernetes debugging applications](https://kubernetes.io/docs/tasks/debug/debug-application/)
- [MicroK8s GPU add-on](https://canonical.com/microk8s/docs/addon-gpu/)

## Next Step

Continue with Chapter 7: STACKIT Expansion.
