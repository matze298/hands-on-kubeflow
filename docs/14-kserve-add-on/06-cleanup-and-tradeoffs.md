# Cleanup and Tradeoffs

This page cleans up the optional KServe resources and summarizes when KServe is worth using.

## What You Will Build

You will create:

```text
infra/kserve/cleanup.md
```

## Create the Cleanup Notes

Create `infra/kserve/cleanup.md`:

```markdown
# KServe Cleanup

This file records the cleanup path for the optional KServe add-on.

Delete tutorial InferenceServices first, then optional secrets and service accounts. Remove the KServe controller only when no other local experiments depend on it.
```

## Delete Tutorial InferenceServices

```bash
kubectl delete -f infra/kserve/tutorial-model.yaml --ignore-not-found
kubectl delete -f infra/kserve/sklearn-iris.yaml --ignore-not-found
```

Verify:

```bash
kubectl -n kubeflow-by-doing get inferenceservice
kubectl -n kubeflow-by-doing get pods | grep -E "sklearn-iris|tutorial-image-classifier" || true
```

## Delete KServe Storage Credentials

If no other KServe examples use local MinIO:

```bash
kubectl delete -f infra/kserve/service-account.yaml --ignore-not-found
kubectl delete -f infra/kserve/minio-secret.yaml --ignore-not-found
```

This does not delete Chapter 4's `artifact-store-credentials` secret. The KServe secret is separate because it uses KServe-specific storage annotations.

## Remove Local Images

Optional local Docker cleanup:

```bash
docker rmi kubeflow-by-doing/kserve:local
```

MicroK8s image cleanup is usually not necessary for a local tutorial. If disk space matters, inspect MicroK8s images:

```bash
sudo microk8s ctr images ls | grep kubeflow-by-doing
```

## Remove KServe Itself

Only remove KServe when you are done with the optional add-on:

```bash
kubectl delete namespace kserve --ignore-not-found
```

Depending on the install path, cluster-scoped CRDs and dependency components may remain. Inspect before deleting them:

```bash
kubectl get crd | grep serving.kserve.io
kubectl get namespaces
```

For a completely clean local cluster, use the FAQ's `MicroK8s` reset procedure instead of manually deleting every optional dependency one by one.

## What KServe Improved

KServe adds:

- a standard `InferenceService` API
- controller-managed serving workloads
- built-in runtimes for common model formats
- custom predictor support
- storage initializer integration
- a path toward autoscaling and rollout strategies
- a model-serving vocabulary that is common across teams

For platform teams, that standard API is the main benefit.

## What KServe Costs

KServe also adds:

- CRDs and controller lifecycle
- webhooks and certificates
- ingress or Gateway API assumptions
- storage credential conventions
- serving runtime compatibility constraints
- another layer to debug between model code and pods

For a single local model, a plain FastAPI `Deployment` is easier. KServe becomes useful when repeated model serving is itself a platform requirement.

## When To Use Which

| Situation | Prefer |
|---|---|
| first local model smoke test | FastAPI `Deployment` |
| teaching Kubernetes serving primitives | FastAPI `Deployment` |
| one-off internal demo | FastAPI or KServe, depending on team familiarity |
| many models with common serving conventions | KServe |
| platform-managed serving with standard APIs | KServe |
| built-in runtime fits the artifact format | KServe built-in runtime |
| custom Python model loading is required | KServe custom predictor |
| serverless scale-to-zero is important | KServe Knative mode or another serverless serving layer |
| high-throughput LLM serving | KServe plus an optimized runtime such as vLLM, SGLang, Triton, or TensorRT-LLM |

## How This Maps to Cloud

In cloud or shared Kubernetes, revisit:

- ingress or Gateway API design
- TLS and DNS
- identity and object-storage access
- image registry and pull secrets
- autoscaling settings
- resource requests and limits
- GPU scheduling for inference
- monitoring and alerting
- rollout strategy

The local chapter proves mechanics. It is not a production serving architecture by itself.

## Acceptance Criteria

You are done when:

- optional `InferenceService` resources are deleted or intentionally kept
- KServe storage credentials are deleted or intentionally kept
- you know whether KServe should remain installed in the local cluster
- you can explain the tradeoff between Chapter 5 FastAPI serving and KServe-managed serving

## References

- [KServe Kubernetes deployment installation](https://kserve.github.io/website/docs/admin-guide/kubernetes-deployment)
- [KServe custom predictor guide](https://kserve.github.io/website/docs/model-serving/predictive-inference/frameworks/custom-predictor)
- [KServe model storage overview](https://kserve.github.io/website/docs/model-serving/storage/overview)

## Next Step

Return to [Conclusion and Future Reading](../11-conclusion/00-overview.md) or continue with the optional [Flyte Add-On](../12-flyte-add-on/00-overview.md) if you want to compare orchestration choices.
