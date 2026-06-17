# Optional KServe Add-On

This optional chapter turns the Chapter 5 KServe preview into a hands-on local serving track.

The core tutorial used a plain FastAPI `Deployment` and `Service` first. That was intentional: it showed the model server, container, pod, service, and smoke test without hiding them behind a controller.

KServe adds a higher-level serving API on top of those Kubernetes primitives.

## Prerequisites

Before starting or resuming this add-on, make sure:

- the `k3s-kubeflow` `k3s` profile is running from [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md)
- the Chapter 5 serving path works from [Local Serving](../05-local-serving/00-overview.md)
- MinIO is running and contains a tutorial model artifact from [Install Local Object Storage](../04-artifacts-and-tracking/01-install-minio.md) and [Trace Lineage](../04-artifacts-and-tracking/04-trace-lineage.md)
- the serving image can be built from [Containerize Serving](../05-local-serving/02-containerize-serving.md)
- KServe itself does not need to be installed yet; this add-on starts with [Install KServe](01-install-kserve.md)

## What You Will Build

You will add an optional KServe path that:

```text
install KServe Standard mode on k3s
  ↓
deploy a first built-in sklearn InferenceService
  ↓
connect KServe to local MinIO
  ↓
adapt the tutorial model server to KServe's custom predictor pattern
  ↓
serve a promoted tutorial model from object storage
  ↓
verify and debug the KServe-managed workload
  ↓
clean up the optional serving stack
```

Target files created while following this chapter:

```text
infra/kserve/
├── README.md
├── sklearn-iris.yaml
├── iris-input.json
├── minio-secret.yaml
├── service-account.yaml
├── tutorial-model.yaml
└── cleanup.md

src/kubeflow_by_doing/
└── kserve_model.py

Dockerfile.kserve
```

The checked-in repository does not need these files before you reach this optional chapter. Treat them as build-along target files.

## Why This Is Optional

KServe is useful when serving itself becomes a platform concern:

- standard model-serving resources
- built-in serving runtimes
- custom serving runtimes
- storage initializer integration
- autoscaling hooks
- rollout patterns
- a path toward inference platform operations

It is not required to understand the core Kubeflow Pipelines workflow.

## Standard Mode

This chapter uses KServe **Standard** mode.

Standard mode creates normal Kubernetes resources such as `Deployment`, `Service`, `Ingress` or Gateway API resources, and `HorizontalPodAutoscaler`. That makes it easier to inspect with the Kubernetes tools used throughout the tutorial.

The alternative is Knative mode. Knative mode is valuable for serverless scale-to-zero patterns, but it adds another platform layer before the reader needs it.

## Relationship to Chapter 5

Chapter 5:

```text
FastAPI app
  ↓
Docker image
  ↓
Deployment
  ↓
Service
  ↓
manual smoke test
```

This add-on:

```text
model artifact
  ↓
KServe InferenceService
  ↓
KServe-managed predictor pod
  ↓
KServe route / service
  ↓
standard inference request
```

The model is still the same small image classifier. The platform boundary changes.

## Chapter Pages

```text
00-overview.md
01-install-kserve.md
02-first-inferenceservice.md
03-storage-and-minio.md
04-serve-the-tutorial-model.md
05-verify-and-debug.md
06-cleanup-and-tradeoffs.md
```

## Acceptance Criteria

You are done with this add-on when:

- KServe is installed in the local `k3s` cluster
- a built-in `InferenceService` reaches `READY=True`
- KServe can read model artifacts from local MinIO
- the tutorial model is served through a KServe-managed predictor
- you can inspect the generated Kubernetes resources
- you can explain when KServe is worth the extra platform surface

## References

- [KServe Kubernetes deployment installation](https://kserve.github.io/website/docs/admin-guide/kubernetes-deployment)
- [KServe quickstart guide](https://kserve.github.io/website/docs/getting-started/quickstart-guide)
- [KServe custom predictor guide](https://kserve.github.io/website/docs/model-serving/predictive-inference/frameworks/custom-predictor)
- [KServe model storage overview](https://kserve.github.io/website/docs/model-serving/storage/overview)

## Next Step

Start with [Install KServe](01-install-kserve.md).
