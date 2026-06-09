# Capstone Contract

This page defines what the capstone must prove.

## The Contract

The capstone workflow must run from a clean repository state and produce an inspectable platform run.

The final pipeline is:

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

## What Counts as Success

A successful capstone run has:

```text
KFP run succeeded
dataset artifact exists
validation report exists
model artifact exists
metrics artifact exists
promotion or registry record exists
lineage record exists
model server updated or confirmed
smoke test passed
```

## What Stays Local

The capstone is still local-first.

Default target:

```text
MicroK8s
```

Fallback:

```text
kind CPU path
```

Cloud mapping comes at the end. Do not make the capstone require STACKIT or another cloud provider.

## What Must Be Durable

These must not live only in a temporary pod filesystem:

```text
dataset manifest
validation report
model artifact
training summary
metrics
promotion / registry record
lineage record
```

They should be written to object storage using the Chapter 4 artifact layout:

```text
s3://kubeflow-by-doing/runs/<run_id>/
├── datasets/
├── validation/
├── models/
├── metrics/
├── reports/
├── predictions/
├── registry/
└── lineage/
```

## What Must Be Parameterized

The capstone pipeline should expose:

```text
run_id
dataset_uri
accelerator
gpu_count
cpu_image
gpu_image
serve_image
min_accuracy
deploy_after_promotion
git_sha
```

## Create `reports/capstone-runbook.md`

Create:

```bash
mkdir -p reports
```

Create `reports/capstone-runbook.md`:

```markdown
# Capstone Runbook

## Goal

Run the full local Kubeflow by Doing workflow end to end.

## Pipeline

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

## Required Services

- Kubernetes cluster: MicroK8s preferred, kind fallback
- Kubeflow Pipelines
- object storage: MinIO locally
- optional MLflow
- model server Deployment

## Required Images

- training image
- optional GPU training image
- serving image

## Required Secrets

- `artifact-store-credentials`
- optional registry pull secret

## Run ID

Use a unique run ID:

```bash
export KBD_RUN_ID="capstone-local-$(date +%Y%m%d-%H%M%S)"
```

## Success Criteria

- KFP run succeeds
- model artifact exists in object storage
- metrics artifact exists in object storage
- lineage artifact exists in object storage
- promotion or registry record exists
- model server responds to `/healthz`
- model server responds to `/predict`
```

## Local Preflight

Run:

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
uv run mkdocs build --strict
```

Check cluster:

```bash
kubectl get nodes
kubectl get pods -A
```

Check KFP:

```bash
kubectl -n kubeflow get pods
```

Check object storage secret:

```bash
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
```

## Common Problems

### Capstone tries to do too much at once

Run each stage independently:

```text
ingest
validate
train
evaluate
register
deploy
smoke test
```

### Local GPU breaks the capstone

Run CPU fallback first:

```text
accelerator=cpu
gpu_count=0
```

Then run GPU.

### Serving breaks after successful training

Check the serving chapter independently before debugging the full capstone.

## Acceptance Criteria

You are done when:

- capstone runbook exists
- durable artifact requirements are clear
- pipeline parameters are clear
- CPU fallback is the first recommended run
- success criteria are explicit

## Next Step

Continue with [Ingest and Validate](02-ingest-and-validate.md).
