# First InferenceService

This page deploys a known-good built-in KServe runtime before serving the tutorial model.

Do this first. It separates KServe installation problems from tutorial model problems.

## What You Will Build

You will create:

```text
infra/kserve/
├── sklearn-iris.yaml
└── iris-input.json
```

The model is the public sklearn Iris example used by the KServe docs.

## Create the InferenceService

Create `infra/kserve/sklearn-iris.yaml`:

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-iris
  namespace: kubeflow-by-doing
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      protocolVersion: v2
      runtime: kserve-sklearnserver
      storageUri: gs://kfserving-examples/models/sklearn/1.0/model
      resources:
        requests:
          cpu: "250m"
          memory: "512Mi"
        limits:
          cpu: "1"
          memory: "1Gi"
```

Apply:

```bash
kubectl apply -f infra/kserve/sklearn-iris.yaml
```

## Watch Readiness

```bash
kubectl -n kubeflow-by-doing get inferenceservice sklearn-iris
kubectl -n kubeflow-by-doing get pods
```

Expected shape:

```text
NAME           URL                                      READY
sklearn-iris   http://sklearn-iris...                   True
```

If `READY` is not `True`, go to [Verify and Debug](05-verify-and-debug.md) before continuing.

## Inspect Generated Resources

KServe creates lower-level Kubernetes resources for the predictor.

```bash
kubectl -n kubeflow-by-doing get deploy
kubectl -n kubeflow-by-doing get svc
kubectl -n kubeflow-by-doing get hpa
```

The exact names include KServe-generated suffixes. Look for names containing:

```text
sklearn-iris
predictor
```

This is the key mental model:

```text
InferenceService is the user-facing resource
KServe controller creates the runtime Kubernetes resources
```

## Create an Input Payload

Create `infra/kserve/iris-input.json`:

```json
{
  "inputs": [
    {
      "name": "input-0",
      "shape": [2, 4],
      "datatype": "FP32",
      "data": [
        [6.8, 2.8, 4.8, 1.4],
        [6.0, 3.4, 4.5, 1.6]
      ]
    }
  ]
}
```

## Send a Request

The official route path depends on the local ingress or gateway installed by KServe. First capture the service hostname:

```bash
export SERVICE_HOSTNAME="$(kubectl -n kubeflow-by-doing get inferenceservice sklearn-iris -o jsonpath='{.status.url}' | cut -d / -f 3)"
echo "$SERVICE_HOSTNAME"
```

If your local ingress is reachable on `localhost:80`, use:

```bash
curl -H "Host: ${SERVICE_HOSTNAME}" \
  -H "Content-Type: application/json" \
  --data @infra/kserve/iris-input.json \
  "http://localhost/v2/models/sklearn-iris/infer"
```

If local ingress is not reachable directly, inspect the generated services and port-forward the predictor service:

```bash
kubectl -n kubeflow-by-doing get svc | grep sklearn-iris
```

Then port-forward the KServe-created predictor service:

```bash
kubectl -n kubeflow-by-doing port-forward svc/<sklearn-iris-service-name> 8081:80
```

In another terminal:

```bash
curl -H "Host: ${SERVICE_HOSTNAME}" \
  -H "Content-Type: application/json" \
  --data @infra/kserve/iris-input.json \
  "http://localhost:8081/v2/models/sklearn-iris/infer"
```

Expected output shape:

```json
{
  "model_name": "sklearn-iris",
  "outputs": [
    {
      "name": "predict",
      "shape": [2],
      "datatype": "INT64"
    }
  ]
}
```

## Why This Test Matters

This model proves:

- KServe CRDs work
- the controller can create predictor workloads
- the default sklearn runtime is installed
- storage initializer can fetch a public model
- local networking can reach a prediction endpoint

Only after this works should you debug the tutorial model path.

## Acceptance Criteria

You are done when:

- `sklearn-iris` reaches `READY=True`
- generated `Deployment` and `Service` resources exist
- an inference request returns a prediction response
- you know whether your local access path is ingress or port-forward

## References

- [KServe sklearn runtime guide](https://kserve.github.io/website/docs/model-serving/predictive-inference/frameworks/sklearn)

## Next Step

Continue with [Storage and MinIO](03-storage-and-minio.md).
