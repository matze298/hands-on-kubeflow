# Local GPU Integration

In this section, we make GPU support a first-class part of the local ML platform.

## What You Will Build

- container-level GPU check
- Kubernetes-level GPU check
- tiny PyTorch CUDA workload
- GPU-enabled KFP training component

## Why This Matters

A local Kubeflow tutorial for ML engineers should not be CPU-only by design. Even if the example model is small, the platform should teach how GPU workloads are requested, scheduled, and debugged.

## Acceptance Criteria

You are done with this section when:

- `nvidia-smi` works inside a container
- a Kubernetes pod can request the GPU
- a PyTorch CUDA test runs in the cluster
- the KFP training component can run with GPU resources
