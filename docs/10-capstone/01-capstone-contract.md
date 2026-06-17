# Capstone Contract

This page defines what the capstone must prove.

This is the assessment chapter for the tutorial. Read the contract first, then build the files yourself. The complete reference files are available behind spoiler blocks so you can compare your solution without turning the capstone into a copy-paste exercise.

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

## What Counts as Success

A successful CPU baseline run has:

```text
KFP run succeeded
dataset artifact exists
validation report exists
model artifact exists
metrics artifact exists
promotion or registry record exists
lineage record exists
MLflow run exists if tracking is enabled
```

A successful deploy-enabled run additionally has:

```text
model server updated or confirmed
smoke test passed
```

## What Stays Local

The capstone is still local-first.

Default target:

```text
k3s
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

The pipeline `artifact_bucket` parameter and the `KBD_ARTIFACT_BUCKET` value in `artifact-store-credentials` must point to the same bucket.

The parameter is used when the pipeline constructs durable artifact URIs. The secret-backed environment value is used by the container code that uploads files. If they differ, the run can upload artifacts to one bucket while recording URIs for another.

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
artifact_bucket
min_accuracy
deploy_after_promotion
git_sha
n_train
n_val
image_size
n_classes
epochs
learning_rate
batch_size
```

## Create `reports/capstone-runbook.md`

Create:

```bash
mkdir -p reports
```

Create `reports/capstone-runbook.md` yourself. It should capture the goal, the final pipeline, required services, required images, required secrets, run ID convention, and success criteria.

??? example "Reference implementation: `reports/capstone-runbook.md`"

    ````markdown
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

    ## Required Services

    - Kubernetes cluster: k3s preferred, kind fallback
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
    - model server responds to `/healthz` when deployment is enabled
    - model server responds to `/predict` when deployment is enabled
    ````

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
