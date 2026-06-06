# KServe Preview

This page introduces KServe conceptually.

The core tutorial uses a simple FastAPI Deployment first because it is transparent and easy to debug.

KServe becomes useful when the serving requirements grow.

## What KServe Adds

KServe provides Kubernetes-native abstractions for model serving, including:

- `InferenceService` custom resources
- standardized model server patterns
- scale-to-zero options depending on the installation mode
- canary rollout patterns
- model storage integration
- inference protocol conventions
- integration with service meshes or gateways in more advanced setups

## Why We Did Not Start with KServe

KServe is powerful, but it adds several concepts at once:

- CRDs
- controller-managed serving
- networking assumptions
- gateway or ingress behavior
- storage initializer behavior
- autoscaling configuration

For a local-first tutorial, it is better to first understand:

```text
model file
  ↓
FastAPI app
  ↓
container
  ↓
Deployment
  ↓
Service
```

Then KServe becomes easier to reason about.

## Mental Mapping

| Simple local serving | KServe equivalent |
|---|---|
| FastAPI app | model server runtime |
| Deployment | `InferenceService` managed workload |
| Service | predictor endpoint |
| ConfigMap model URI | storage URI |
| manual rollout | KServe rollout behavior |
| manual smoke test | inference request to service endpoint |

## Example `InferenceService`

This is a preview only. Do not add this to the core path yet.

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: tiny-image-classifier
  namespace: kubeflow-by-doing
spec:
  predictor:
    model:
      modelFormat:
        name: pytorch
      storageUri: s3://kubeflow-by-doing/runs/manual-kfp-001/models/
```

!!! warning

    This example is intentionally incomplete for the current tutorial state. A real KServe deployment needs KServe installed, compatible networking, storage credentials, and a model format/runtime setup that matches the saved artifact.

## When to Introduce KServe

Introduce KServe when you need:

- a standardized serving abstraction
- more production-like model rollout
- autoscaling
- multiple model versions
- platform-managed inference services
- separation between model artifact and serving runtime

Do not introduce it just to serve the first local model.

## Local KServe Caveats

Local KServe can be more complex than the simple FastAPI Deployment because it may require:

- KServe CRDs and controllers
- cert-manager
- networking configuration
- gateway or ingress setup
- storage credential configuration
- compatible model formats

That complexity is valuable later, but it distracts from the first serving milestone.

## Suggested Future Chapter

A later KServe chapter should follow this sequence:

```text
install KServe locally
  ↓
deploy a minimal sklearn or PyTorch example
  ↓
connect S3 credentials
  ↓
serve the tutorial model
  ↓
compare against FastAPI Deployment
  ↓
discuss production tradeoffs
```

## Acceptance Criteria

You are done when:

- you can explain why the tutorial starts with FastAPI and Kubernetes Deployment
- you can explain what KServe adds
- you understand that KServe is an expansion path, not required for the first local serving workflow

## References

- [KServe documentation](https://kserve.github.io/website/latest/)
- [KServe InferenceService concept](https://kserve.github.io/website/latest/modelserving/v1beta1/)
- [KServe runtimes](https://kserve.github.io/website/latest/modelserving/servingruntimes/)

## Next Step

Continue with Chapter 6: Local GPU Integration.
