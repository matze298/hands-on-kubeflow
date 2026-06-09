# Capstone

The capstone combines the core tutorial into one end-to-end local ML platform.

By this point, you have built the pieces separately:

```text
local Kubernetes / MicroK8s
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
record_or_register_model
  ↓
deploy_model
  ↓
smoke_test_endpoint
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
├── record_or_register_model.py
├── deploy_model.py
└── smoke_test_model.py

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
- the served endpoint can be smoke-tested
- the same design maps to STACKIT or another cloud provider

## Local Platform Target

Default local target:

```text
MicroK8s
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
