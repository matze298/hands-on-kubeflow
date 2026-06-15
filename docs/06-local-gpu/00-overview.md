# Local GPU

Chapter 1 already proved the local GPU path at the container and cluster levels.

Chapter 6 does one thing only:

```text
make the Kubeflow training path GPU-aware
```

The point is not to re-teach host GPU setup. The point is to close the loop from a working local GPU-capable cluster to a KFP step that explicitly requests the GPU.

## Updated Cluster Story

For later chapters, this tutorial treats **minikube** as the default local ML/Kubeflow platform.

Use:

```text
minikube = default local GPU-capable platform
kind      = fallback for readers without the GPU-capable local setup
```

Chapter 1 used `kind` for the initial Kubernetes starter path because it is lightweight and easy to reset. For GPU-aware Kubeflow workflows, minikube is the better local default because it more closely resembles a real single-node ML platform and has a dedicated GPU add-on.

## What You Will Build

You will update the training path so that:

- the training component can request `nvidia.com/gpu`
- the same pipeline still works without GPU through a CPU fallback path
- the GPU-enabled component image remains compatible with the local cluster
- GPU scheduling failures are visible from KFP and Kubernetes

## Why This Matters

An ML platform is not GPU-ready just because `nvidia-smi` works in a terminal.

For Kubeflow, the important path is:

```text
KFP component
  ↓
Kubernetes Pod
  ↓
requests nvidia.com/gpu
  ↓
scheduled onto GPU-capable node
  ↓
container image has CUDA-compatible PyTorch
  ↓
training code uses cuda
```

## What This Chapter Does Not Repeat

This chapter does not repeat:

- host NVIDIA driver installation
- Docker GPU runtime setup
- basic Kubernetes GPU enablement
- `nvidia-smi` smoke tests
- Kubernetes device-plugin theory

Those were covered earlier.

## Chapter Files

```text
docs/06-local-gpu/
├── 00-overview.md
├── 01-cluster-gpu-readiness.md
├── 02-gpu-training-image.md
├── 03-gpu-aware-kfp-component.md
├── 04-run-gpu-and-cpu-pipelines.md
└── 05-debug-gpu-scheduling.md
```

## Acceptance Criteria

You are done with Chapter 6 when:

- minikube reports GPU capacity through `nvidia.com/gpu`
- the training component can request `nvidia.com/gpu`
- a KFP run succeeds on the GPU path
- the CPU fallback still works when the GPU path is unavailable
- GPU scheduling failures are visible in the pod or KFP logs
- you can explain the difference between container GPU support and KFP GPU integration

## Next Step

Start with [Cluster GPU Readiness](01-cluster-gpu-readiness.md).
