# Kubeflow Pipelines

Kubeflow Pipelines is the workflow layer of this tutorial.

In Chapter 1, you ran Kubernetes workloads manually. In this chapter, you let Kubeflow Pipelines create and manage those workloads for you.

The goal is not to install the full Kubeflow platform yet. The goal is to install standalone Kubeflow Pipelines locally and use it to run a small ML-shaped workflow.

Chapter 2 now assumes you continue on the GPU-capable `minikube` path from Chapter 1. If you are still on the starter `kind` context, switch contexts first in [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md), especially the "Create the GPU-Capable Local Cluster" and "Create the Tutorial Namespace" sections, then return here.

## Prerequisites

Before starting or resuming this chapter, make sure:

- the `kubeflow-gpu` `minikube` profile is running from [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md)
- `kubectl config current-context` reports `kubeflow-gpu`
- the tutorial namespace `kubeflow-by-doing` exists from [Create the Tutorial Namespace](../01-local-kubernetes/02-create-local-cluster.md#create-the-tutorial-namespace)
- the local toolchain from [Install the Local Toolchain](../01-local-kubernetes/01-install-toolchain.md) is available, especially `uv`, `kubectl`, and `minikube`

## What You Will Build

You will build:

- a standalone Kubeflow Pipelines installation in your GPU-capable local Kubernetes cluster
- a local KFP Python development environment
- a first compiled pipeline
- a pipeline run submitted through the UI
- a pipeline run submitted from Python
- a three-step ML-shaped pipeline
- reusable pipeline components
- a debugging workflow for failed KFP steps

## Why This Matters

A local training script is easy to run once.

An MLOps workflow needs more:

- explicit inputs
- explicit outputs
- reproducible containers
- visible run history
- metrics
- artifacts
- failure state
- reruns
- parameterized execution

Kubeflow Pipelines gives you this workflow layer on top of Kubernetes.

The commands in this chapter still work on a CPU-only cluster if you only want the workflow mechanics. The default path from here on, however, is the GPU-capable `minikube` cluster because later PyTorch work assumes that setup.

## Mental Model

In Chapter 1, you manually created a `Job`.

With Kubeflow Pipelines, you write Python pipeline code, compile it to a pipeline specification, and KFP creates Kubernetes workloads for each step.

```text
Python pipeline code
  ↓
compiled pipeline YAML
  ↓
KFP backend
  ↓
Kubernetes pods
  ↓
logs, metrics, artifacts, run history
```

## What We Do Not Cover Yet

This chapter does not cover:

- full Kubeflow platform installation
- multi-user profiles
- Kubeflow Notebooks
- KServe
- production authentication
- cloud deployment
- GPU training components

Those come later.

## Files in This Chapter

The pages below introduce the files you will create as you work through Chapter 2.

```text
docs/02-kubeflow-pipelines/
├── 00-overview.md
├── 01-install-kfp.md
├── 02-first-pipeline.md
├── 03-run-pipeline-from-python.md
├── 04-components-parameters-artifacts.md
├── 05-reusable-components.md
└── 06-debugging-kfp-runs.md
```

## Acceptance Criteria

You are done with Chapter 2 when:

- Kubeflow Pipelines is running in your local cluster
- the KFP UI is reachable through port forwarding
- `uv run python` can compile a KFP pipeline
- a hello-world pipeline completes
- a pipeline can be submitted from Python
- a three-step ML-shaped pipeline produces metrics and artifacts
- you can map a failed KFP step back to a Kubernetes pod

## Next Step

Start with [Install Kubeflow Pipelines](01-install-kfp.md).
