# Capstone

The capstone combines the core tutorial into one end-to-end local ML platform.

By this point, you have built the pieces separately:

```text
local Kubernetes / k3s
Kubeflow Pipelines
local ML workflow
object storage
experiment tracking
serving
local GPU integration
cloud expansion patterns
CI/CD expansion
```

The capstone ties the core path together into one workflow.

## Prerequisites

Before starting or resuming this chapter, make sure:

- the GPU-capable `k3s` cluster is running from [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md)
- standalone Kubeflow Pipelines is installed and reachable from [Install Kubeflow Pipelines](../02-kubeflow-pipelines/01-install-kfp.md)
- the Chapter 3 training workflow exists and its image is loaded from [Containerize Training](../03-local-ml-workflow/05-containerize-training.md)
- MinIO and MLflow are available from [Install Local Object Storage](../04-artifacts-and-tracking/01-install-minio.md) and [Add Experiment Tracking](../04-artifacts-and-tracking/03-add-mlflow.md)
- the local serving image and Kubernetes service path are available from [Containerize Serving](../05-local-serving/02-containerize-serving.md) and [Deploy to Kubernetes](../05-local-serving/03-deploy-to-kubernetes.md)
- GPU execution is optional; use [Local GPU](../06-local-gpu/00-overview.md) if you want the capstone to request `nvidia.com/gpu`

## How to Use the Capstone

Treat this chapter as the end-to-end test for the tutorial.

The pages give you:

- the target contract
- the files to create
- implementation requirements
- hints where the earlier chapters matter
- commands to compile, run, and verify the workflow
- acceptance criteria for each stage

Build the files yourself first. Full reference implementations are placed behind collapsible spoiler blocks. Use them when you are stuck, when you want to compare your solution, or when you need to recover a broken local state.

## Final Pipeline

```text
ingest_data
  ↓
validate_data
  ↓
train_model
  ↓
evaluate_model
  ↓
read_accuracy
  ↓
promote_model
  ↓
write_lineage
  ↓
record_or_register_model
  ↓
deploy_model, if enabled
  ↓
smoke_test_model, if deployed
```

## What You Will Build

You will create or finalize these target files:

```text
src/kubeflow_by_doing/
├── ingest.py
├── validate.py
├── registry.py
└── capstone_report.py

components/
├── ingest_data.py
├── validate_data.py
└── record_or_register_model.py

pipelines/
└── capstone_pipeline.py

tests/
├── test_ingest.py
├── test_validate.py
└── test_registry.py

reports/
└── capstone-runbook.md

compiled/
└── capstone_pipeline.yaml
```

This chapter also reuses earlier component files from the core tutorial:

```text
components/train_model.py
components/evaluate_model.py
components/promote_model.py
components/write_lineage.py
components/deploy_model.py
components/smoke_test_model.py
```

## Why This Matters

The capstone is the first point where the system behaves like a small local ML platform.

The final workflow should prove:

- data enters the system explicitly
- data is validated before training
- model training runs in Kubeflow
- artifacts survive pod deletion
- metrics control promotion
- lineage is recorded
- a promoted model can be served
- the served endpoint can be smoke-tested when deployment is enabled
- the same design maps to STACKIT or another cloud provider

## Local Platform Target

Default local target:

```text
k3s
```

Fallback target:

```text
kind CPU path
```

The capstone should work on CPU first. GPU should remain an explicit parameter.

## Chapter Files

```text
docs/10-capstone/
├── 00-overview.md
├── 01-capstone-contract.md
├── 02-ingest-and-validate.md
├── 03-final-pipeline.md
├── 04-run-the-capstone.md
├── 05-verify-end-to-end.md
└── 06-cloud-mapping.md
```

## Acceptance Criteria

You are done with the capstone when:

- the full workflow runs locally
- the model is trained in Kubeflow
- artifacts are stored outside the pod filesystem
- evaluation controls promotion
- a promoted model can be served
- the served endpoint can be smoke-tested
- the workflow can be mapped to STACKIT or another cloud provider

## Next Step

Start with [Capstone Contract](01-capstone-contract.md).
