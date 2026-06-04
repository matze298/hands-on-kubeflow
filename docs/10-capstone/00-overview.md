# Capstone

The capstone combines the core tutorial into one end-to-end local ML platform.

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

## Acceptance Criteria

You are done with the capstone when:

- the full workflow runs locally
- the model is trained in Kubeflow
- artifacts are stored outside the pod filesystem
- evaluation controls promotion
- a promoted model can be served
- the served endpoint can be smoke-tested
- the workflow can be mapped to STACKIT or another cloud provider
