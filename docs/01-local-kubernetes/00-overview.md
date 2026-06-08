# Local Kubernetes

Kubeflow runs on Kubernetes.

That does not mean you need to become a full-time Kubernetes administrator before using Kubeflow. It does mean that you need to understand the small set of Kubernetes concepts that show up again and again in ML workflows:

- a training run becomes a `Job`
- a running workload becomes a `Pod`
- a model server becomes a `Deployment` and `Service`
- credentials become `Secrets`
- configuration becomes `ConfigMaps`
- artifacts need persistent storage or object storage
- GPUs are requested as schedulable resources
- debugging usually starts with `kubectl logs`, `kubectl describe`, and Kubernetes events

## What You Will Build

You will create a local Kubernetes environment on a Linux or WSL2 Linux development machine with an NVIDIA GPU.

This chapter starts with `kind` as the starter cluster backend.

This chapter also sets up `MicroK8s` on WSL2 as the default local ML platform for the later chapters. Use `kind` as the starter and fallback cluster.

By the end of this chapter, you will have:

- installed the local command-line toolchain
- created a disposable local Kubernetes cluster
- created a tutorial namespace
- run a tiny workload as a Kubernetes `Job`
- debugged common workload failures
- verified local GPU visibility in containers
- prepared the starter cluster for the first Kubernetes exercises
- prepared the `MicroK8s` cluster that the later Kubeflow and ML chapters assume

## Why This Matters

A lot of ML tutorials hide the runtime.

That is fine for a notebook, but it is not enough for MLOps.

In Kubeflow, your training code does not run as a magical Python function. It runs as a container inside Kubernetes. When something fails, the failure is usually visible at the Kubernetes layer:

- the image cannot be pulled
- the pod is pending
- the container crashed
- the process was killed because it used too much memory
- the GPU was not available
- a secret or mounted file was missing

This chapter teaches the minimum Kubernetes operational loop needed to understand those failures.

## Mental Model

| ML concept              | Kubernetes concept                   |
| ----------------------- | ------------------------------------ |
| training run            | `Job`                                |
| running container       | `Pod`                                |
| model API               | `Deployment`                         |
| endpoint inside cluster | `Service`                            |
| credentials             | `Secret`                             |
| runtime settings        | `ConfigMap`                          |
| saved artifacts         | volume or object storage             |
| GPU request             | `resources.limits["nvidia.com/gpu"]` |
| failed run debugging    | logs, describe, events               |

## Files in This Chapter

```text
docs/01-local-kubernetes/
├── 00-overview.md
├── 01-install-toolchain.md
├── 02-create-local-cluster.md
├── 03-first-kubernetes-job.md
├── 04-debugging-basics.md
└── 05-gpu-smoke-test.md
```

## Acceptance Criteria

You are done with Chapter 1 when:

- `kubectl` can talk to your local cluster
- a namespace called `kubeflow-by-doing` exists
- a simple Kubernetes `Job` completes successfully
- you can inspect job logs
- you can debug a deliberately broken pod
- `docker run --gpus all ... nvidia-smi` works
- the `MicroK8s` GPU path is available and a Kubernetes pod can request the GPU

## Next Step

Start with [Install the Local Toolchain](01-install-toolchain.md).
