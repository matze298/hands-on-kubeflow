# Generic Cloud Expansion

Chapter 8 generalizes the local and STACKIT setup to other managed Kubernetes providers.

The goal is not to create a full AWS, Azure, or Google Cloud tutorial. The goal is to make the tutorial architecture portable:

```text
Kubernetes provider changes
pipeline code stays mostly the same
```

## What You Will Learn

You will learn:

- what changes between Kubernetes providers
- what should remain portable
- where costs usually appear
- how to structure environment overlays
- how to keep pipeline code provider-neutral
- how to plan cleanup before creating cloud resources

## What You Will Build

You will create provider-neutral overlay files:

```text
infra/cloud/
├── README.md
├── env.example
├── provider-matrix.md
├── overlays/
│   ├── aws.env.example
│   ├── azure.env.example
│   ├── gcp.env.example
│   └── generic.env.example
├── secrets/
│   ├── artifact-store-secret.template.yaml
│   └── image-pull-secret.md
├── checks/
│   ├── cluster-check.sh
│   ├── object-storage-check.py
│   ├── object-storage-pod-check.yaml
│   └── image-pull-check.yaml
└── cleanup/
    ├── cleanup-checklist.md
    └── delete-object-prefixes.py
```

## Provider-Neutral Rule

The pipeline should not know whether it runs on:

```text
MicroK8s
STACKIT SKE
AWS EKS
Azure AKS
Google GKE
another managed Kubernetes provider
```

Instead, the pipeline receives parameters and environment:

```text
image names
object storage endpoint
bucket
secrets
accelerator mode
pipeline root
```

## What Should Stay Portable

Keep these stable:

- Python package layout
- KFP component interfaces
- pipeline parameters
- artifact layout
- image names passed as parameters
- Kubernetes Secret key names
- cleanup checklist structure

## What Usually Changes

Expect these to change per provider:

- cluster creation
- node pools
- GPU setup
- container registry host
- image pull authentication
- object storage endpoint
- object storage authentication
- load balancers and ingress
- IAM / workload identity
- storage classes
- cost model

## Chapter Files

```text
docs/08-cloud-expansion/
├── 00-overview.md
├── 01-portability-model.md
├── 02-provider-overlays.md
├── 03-cloud-secrets-and-registries.md
├── 04-object-storage-abstraction.md
├── 05-gpu-and-node-pools.md
├── 06-cost-and-cleanup.md
└── 07-provider-checklist.md
```

## Acceptance Criteria

You are done with Chapter 8 when:

- you can identify provider-specific configuration
- you can keep pipeline code provider-neutral
- you can structure environment overlays
- you can configure image pulls through Kubernetes Secrets or provider-native identity
- you can keep the artifact layout stable across providers
- you can plan cleanup for cloud resources before creating them

## Next Step

Start with [Portability Model](01-portability-model.md).
