# Local GPU

Chapter 1 already proved the local GPU path at the container and cluster levels.

Chapter 6 does one thing only:

```text
make the Kubeflow training path GPU-aware
```

The point is not to re-teach host GPU setup. The point is to close the loop from a working local GPU-capable cluster to a KFP step that explicitly requests the GPU.

## Prerequisites

Before starting or resuming this chapter, make sure:

- the GPU-capable `k3s` cluster is running from [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md)
- the GPU smoke tests from [GPU Smoke Test](../01-local-kubernetes/05-gpu-smoke-test.md) pass on your machine
- standalone Kubeflow Pipelines is installed and reachable from [Install Kubeflow Pipelines](../02-kubeflow-pipelines/01-install-kfp.md)
- the Chapter 3 training workflow exists from [Containerize Training](../03-local-ml-workflow/05-containerize-training.md) and [Train in Kubeflow](../03-local-ml-workflow/06-train-in-kubeflow.md)
- use the CPU fallback path if you are resuming on `kind` instead of the GPU-capable `k3s` setup

## Updated Cluster Story

For later chapters, this tutorial treats **k3s** as the default local ML/Kubeflow platform.

Use:

```text
k3s      = default local GPU-capable platform
kind      = fallback for readers without the GPU-capable local setup
```

Chapter 1 used `kind` for the initial Kubernetes starter path because it is lightweight and easy to reset. For GPU-aware Kubeflow workflows on WSL2, k3s is the better local default because it can use Docker's NVIDIA runtime path directly while still behaving like a normal single-node Kubernetes cluster.

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

- k3s reports GPU capacity through `nvidia.com/gpu`
- the training component can request `nvidia.com/gpu`
- a KFP run succeeds on the GPU path
- the CPU fallback still works when the GPU path is unavailable
- GPU scheduling failures are visible in the pod or KFP logs
- you can explain the difference between container GPU support and KFP GPU integration

## Next Step

Start with [Cluster GPU Readiness](01-cluster-gpu-readiness.md).
