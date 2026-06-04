# Local Kubernetes

In this section, we build the local Kubernetes foundation for the tutorial.

The goal is not to become a Kubernetes administrator. The goal is to understand enough Kubernetes to run, inspect, and debug ML workloads through Kubeflow.

## What You Will Build

- local Kubernetes cluster
- basic namespace structure
- first Kubernetes Job
- debugging workflow
- GPU-readiness checks

## Why This Matters

Kubeflow does not hide Kubernetes. Kubeflow turns ML workflows into Kubernetes-native workloads. To use Kubeflow well, an ML engineer needs to understand what is actually running in the cluster.

## Acceptance Criteria

You are done with this section when:

- you can create and delete the local cluster
- you can run a Kubernetes Job
- you can inspect logs and events
- you can explain why a failed pod failed
- you can verify whether the local GPU is visible to containerized workloads
