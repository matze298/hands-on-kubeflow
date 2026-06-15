# STACKIT Expansion

Chapter 7 moves the local workflow to STACKIT.

The local core path taught the concepts:

```text
local Kubernetes / minikube
  ↓
Kubeflow Pipelines
  ↓
local object storage
  ↓
local images
  ↓
local serving
```

This chapter maps the same architecture to STACKIT:

```text
STACKIT Kubernetes Engine
  ↓
Kubeflow Pipelines
  ↓
STACKIT Object Storage
  ↓
STACKIT Container Registry or another registry
  ↓
optional GPU node pool
  ↓
cost-aware cleanup
```

## What You Will Build

You will create the cloud expansion target files during the tutorial:

```text
infra/stackit/
├── README.md
├── env.example
├── kubeconfig.md
├── object-storage-secret.yaml
├── container-registry-secret.yaml
├── kfp-install.md
├── image-pull-smoke.yaml
├── object-storage-smoke.yaml
├── gpu-check.yaml
└── cleanup.md

scripts/
├── stackit-build-and-push.sh
├── stackit-create-object-bucket.py
├── stackit-verify-artifacts.py
└── stackit-delete-tutorial-objects.py
```

## Why This Matters

Cloud expansion is not a new ML workflow.

It is a change in infrastructure boundaries:

| Local | STACKIT |
|---|---|
| minikube / kind | STACKIT Kubernetes Engine |
| local image loading | container registry |
| MinIO | STACKIT Object Storage |
| local GPU | GPU node pool |
| port-forward only | port-forward first, ingress/load balancer later |
| disposable cluster | cost-managed cloud resources |

The pipeline code should change as little as possible.

## Prerequisites

To complete the hands-on deployment parts of this chapter, you need:

- a STACKIT user account
- a STACKIT customer account
- a STACKIT project linked to a billing account
- a payment method on that billing account
- permission to access or create an SKE cluster in the project

You may also need budget or approval for the cloud resources the chapter creates, including SKE worker nodes, object storage, and any optional GPU node pool.

If you do not have a STACKIT account, do not want to use one, or do not want to spend money on cloud resources, you can still read the chapter and skip the deployment steps. The chapter is a hands-on example of applying the local Kubeflow workflow to a real Kubernetes provider; it is not a requirement for the rest of the tutorial.

## Scope

This chapter focuses on:

- mapping the local architecture to STACKIT
- connecting `kubectl` to SKE
- pushing images to a registry
- replacing MinIO with STACKIT Object Storage
- deploying KFP into SKE
- running the existing pipeline
- optionally validating GPU workloads
- explicit cost-control and cleanup

This chapter does **not** cover:

- production hardening
- GitOps
- ingress/TLS
- multi-tenant Kubeflow
- enterprise IAM design
- KServe production rollout
- monitoring and alerting

Those are later expansion topics.

## Cluster Story

For this repo:

```text
minikube = default local ML/Kubeflow platform
kind      = fallback and starter path
SKE       = cloud expansion path
```

The STACKIT chapter should not rewrite the local chapters. It should map the local workflow to managed infrastructure.

## Chapter Files

```text
docs/07-stackit-expansion/
├── 00-overview.md
├── 01-stackit-architecture.md
├── 02-create-ske-cluster.md
├── 03-container-registry-and-images.md
├── 04-object-storage-and-secrets.md
├── 05-run-kfp-on-stackit.md
├── 06-gpu-node-pool.md
└── 07-cost-control-and-cleanup.md
```

## Acceptance Criteria

You are done with Chapter 7 when:

- `kubectl` can access a STACKIT Kubernetes Engine cluster
- the local training and serving images are available from a registry reachable by SKE
- STACKIT Object Storage credentials are available as Kubernetes Secrets
- the artifact layout still uses `s3://kubeflow-by-doing/runs/<run_id>/...`
- Kubeflow Pipelines runs in SKE
- the existing pipeline can run against cloud object storage
- optional GPU node-pool validation works, or the CPU path is documented
- cleanup steps are explicit enough to avoid idle cloud cost

## Next Step

Start with [STACKIT Architecture](01-stackit-architecture.md).
