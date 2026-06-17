# Verify and Debug

This page gives the debugging loop for KServe-managed serving.

The goal is to map KServe state back to Kubernetes resources, just like the KFP debugging chapter mapped pipeline state back to pods, logs, and events.

## What You Will Verify

You will inspect:

- `InferenceService` status
- generated `Deployment`
- generated `Service`
- predictor pod logs
- storage initializer behavior
- object-storage access
- request path and host header

## Check the InferenceService

```bash
kubectl -n kubeflow-by-doing get inferenceservice
kubectl -n kubeflow-by-doing describe inferenceservice tutorial-image-classifier
```

Look for:

```text
Ready: True
URL: ...
```

If `Ready` is false, read the status conditions before looking elsewhere:

```bash
kubectl -n kubeflow-by-doing get inferenceservice tutorial-image-classifier -o yaml
```

The status often tells you whether the failure is storage, revision creation, routing, or predictor readiness.

## Inspect Generated Kubernetes Resources

```bash
kubectl -n kubeflow-by-doing get deploy
kubectl -n kubeflow-by-doing get pods
kubectl -n kubeflow-by-doing get svc
kubectl -n kubeflow-by-doing get hpa
```

Filter by service name:

```bash
kubectl -n kubeflow-by-doing get all | grep tutorial-image-classifier
```

KServe owns these generated resources. Change the `InferenceService` manifest first, then let the controller reconcile the lower-level resources.

## Inspect Predictor Pods

Find the pod:

```bash
kubectl -n kubeflow-by-doing get pods | grep tutorial-image-classifier
```

Describe it:

```bash
kubectl -n kubeflow-by-doing describe pod <pod-name>
```

Read logs:

```bash
kubectl -n kubeflow-by-doing logs <pod-name> -c kserve-container
```

If the pod has an init container, inspect its logs too:

```bash
kubectl -n kubeflow-by-doing logs <pod-name> -c storage-initializer
```

Container names can differ by KServe version. Use `kubectl describe pod` to confirm the exact names.

## Debug Storage Failures

Storage failures usually show up before the predictor container starts.

Check:

```bash
kubectl -n kubeflow-by-doing get serviceaccount kserve-minio-reader -o yaml
kubectl -n kubeflow-by-doing get secret kserve-minio-credentials -o yaml
kubectl -n minio get svc minio
```

Common causes:

| Symptom | Likely cause |
|---|---|
| `NoSuchBucket` | bucket name in `STORAGE_URI` does not exist |
| connection refused | wrong S3 endpoint or MinIO not running |
| TLS error | `serving.kserve.io/s3-usehttps` does not match MinIO setup |
| access denied | secret keys are wrong or not attached to the service account |
| file not found in predictor | `STORAGE_URI` points at the wrong prefix |

For this tutorial, `STORAGE_URI` should point at:

```text
s3://kubeflow-by-doing/runs/<run_id>/models/
```

and the predictor should load:

```text
/mnt/models/model.pt
```

## Debug Image Failures

If the pod cannot pull the image:

```bash
kubectl -n kubeflow-by-doing describe pod <pod-name>
```

Look for:

```text
ImagePullBackOff
ErrImagePull
```

For local k3s, rebuild the image and confirm Docker can see it:

```bash
docker build -f Dockerfile.kserve -t kubeflow-by-doing/kserve:local .
docker images kubeflow-by-doing/kserve:local
```

Keep:

```yaml
imagePullPolicy: IfNotPresent
```

for the local image path.

## Debug Request Routing

KServe routing often depends on the `Host` header.

Capture:

```bash
export SERVICE_HOSTNAME="$(kubectl -n kubeflow-by-doing get inferenceservice tutorial-image-classifier -o jsonpath='{.status.url}' | cut -d / -f 3)"
echo "$SERVICE_HOSTNAME"
```

Then include it in `curl`:

```bash
curl -v \
  -H "Host: ${SERVICE_HOSTNAME}" \
  -H "Content-Type: application/json" \
  --data @outputs/kserve-input.json \
  "http://localhost:8082/v1/models/tutorial-image-classifier:predict"
```

If you get `404`, check:

- host header
- path
- model name
- whether you are hitting the ingress or a port-forwarded service

## Debug Predictor Code

If the custom predictor starts and then crashes:

```bash
kubectl -n kubeflow-by-doing logs <pod-name> -c kserve-container --previous
```

Common causes:

| Symptom | Fix |
|---|---|
| `model.pt` missing | verify `STORAGE_URI` and MinIO prefix |
| `KeyError: image_size` | model file is not from the tutorial training code |
| tensor shape mismatch | request payload image size differs from training image size |
| import error | rebuild `Dockerfile.kserve` after dependency changes |

## Compare Against the FastAPI Deployment

Use this comparison to decide whether the KServe issue is platform-specific:

```bash
kubectl -n kubeflow-by-doing get deploy model-server
kubectl -n kubeflow-by-doing port-forward svc/model-server 8000:8000
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

If FastAPI serving works but KServe serving does not, focus on:

- KServe install
- `InferenceService`
- storage initializer
- custom predictor image
- KServe request path and host header

If both fail, focus on:

- model artifact
- serving code
- request payload
- image build

## Acceptance Criteria

You are done when:

- you can read `InferenceService` conditions
- you can find the generated predictor pod
- you can inspect storage initializer logs
- you can distinguish storage, image, routing, and predictor-code failures
- you can compare KServe serving against the Chapter 5 FastAPI serving path

## References

- [KServe model storage overview](https://kserve.github.io/website/docs/model-serving/storage/overview)
- [KServe S3 storage provider](https://kserve.github.io/website/docs/model-serving/storage/providers/s3)

## Next Step

Continue with [Cleanup and Tradeoffs](06-cleanup-and-tradeoffs.md).
