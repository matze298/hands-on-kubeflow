# Local GPU

Chapter 1 already proved the local GPU path at the container and cluster levels.

Chapter 6 does one thing only: it makes the Kubeflow training path GPU-aware.

The point is not to re-teach GPU setup. The point is to close the loop from a working local GPU cluster to a KFP step that explicitly requests the GPU.

## What You Will Build

You will update the training path so that:

- the training component requests `nvidia.com/gpu`
- the same pipeline still works without GPU if you use the CPU fallback path
- the GPU-enabled component image remains compatible with the local cluster
- the Kubeflow run makes GPU scheduling failures visible

## Why This Matters

An ML platform is not GPU-ready just because `nvidia-smi` works in a terminal.

You still need to know:

- how to request the accelerator from a KFP step
- how the pod behaves when scheduling succeeds or fails
- how to keep a CPU fallback path available when the GPU path is unavailable

That is the real difference between “GPU visible” and “GPU integrated into the workflow”.

## Focus

This chapter does not repeat:

- host GPU installation
- Docker GPU runtime setup
- basic Kubernetes GPU enablement

Those are covered earlier.

Instead, this chapter focuses on the KFP delta:

- component resource requests
- image compatibility
- KFP scheduling behavior
- debugging failed GPU runs

## Acceptance Criteria

You are done with this section when:

- the training component can request `nvidia.com/gpu`
- a KFP run succeeds on the GPU path
- the CPU fallback still works when the GPU path is unavailable
- GPU scheduling failures are visible in the pod or KFP logs
- you can explain the difference between container GPU support and KFP GPU integration
