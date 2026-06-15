# Course Architecture

This tutorial is local-first and GPU-aware.

The core path starts with `kind` for the first Kubernetes basics, then uses `minikube` on WSL2 as the default local ML platform. Later chapters expand the same workflow to STACKIT, managed Kubernetes patterns, and CI/CD. Production-style serving and full Kubeflow platform operations are next-step topics once the core workflow is working. A final optional add-on compares the workflow with Flyte instead of Kubeflow Pipelines.

## Core Architecture

```text
Linux / WSL2 dev machine
├── kind starter cluster
├── NVIDIA GPU
├── Docker or compatible container runtime
├── minikube default cluster for the ML path
├── Kubeflow Pipelines
├── local object storage
├── optional marimo exploration
├── containerized PyTorch training
├── evaluation gate
└── local model serving
```

## Expansion Architecture

```text
local workflow
  ↓
STACKIT SKE or another managed Kubernetes provider
  ↓
cloud object storage
  ↓
container registry
  ↓
GPU node pool
  ↓
CI/CD
  ↓
next-step production serving and platform operations
  ↓
optional Flyte orchestrator comparison
```

## Why Local First?

Starting with cloud infrastructure creates too much incidental complexity.

A local setup lets the reader learn the core ideas first:

- what Kubernetes runs
- how Kubeflow Pipelines maps ML steps to containers
- how artifacts move between steps
- how model promotion works
- how serving fits into the workflow
- how to debug failed runs

Once that is clear, cloud is mostly a change in infrastructure boundaries.

This tutorial teaches the open Kubernetes-native path so the mechanics are visible. If the goal is to ship quickly inside one cloud provider, a managed ML platform may be a better operational choice. The full tradeoff belongs at the end, after the reader has built the workflow, in [Conclusion and Future Reading](../11-conclusion/00-overview.md). Flyte appears after that as an optional orchestrator comparison, not as a replacement for the Kubeflow course path.

## Why GPU-Aware?

ML engineers often need to know whether their code still behaves correctly when moved from local scripts to containerized GPU workloads.

Therefore, the tutorial treats local NVIDIA GPU support as part of the core engineering story.

The training task remains small, but the platform should be able to run GPU workloads.
