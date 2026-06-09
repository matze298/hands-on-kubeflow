# Connect Pipeline to Serving

This page connects the training pipeline to the local serving deployment.

The first version stays simple:

```text
train
  ↓
evaluate
  ↓
if metric passes:
      promote
      update model-server ConfigMap
      restart deployment
      smoke-test endpoint
```

## What You Will Build

You will create:

```text
manifests/model-server/rbac.yaml
components/deploy_model.py
components/smoke_test_model.py
```

You will update:

```text
pipelines/image_classification_pipeline.py
```

## Why This Matters

The platform loop should not stop at model training.

We want a visible path from:

```text
model passes evaluation
```

to:

```text
model is served
```

This chapter keeps deployment deliberately transparent by using normal Kubernetes resources.

## Serving Update Strategy

The model server reads its model URI from:

```text
ConfigMap/model-server-config
```

To deploy a new model, the pipeline can:

1. patch `KBD_MODEL_S3_URI`
2. restart the `model-server` Deployment
3. wait for readiness
4. run a smoke test

This is not a production rollout strategy. It is a clear local-first learning strategy.

## Create Local RBAC

For a pipeline component to patch a ConfigMap or restart a Deployment, the pod needs Kubernetes permissions.

For a local tutorial, create scoped RBAC for the tutorial namespace.

Create `manifests/model-server/rbac.yaml`:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pipeline-deployer
  namespace: kubeflow-by-doing
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: model-server-deployer
  namespace: kubeflow-by-doing
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "patch", "update"]
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "patch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: model-server-deployer
  namespace: kubeflow-by-doing
subjects:
  - kind: ServiceAccount
    name: pipeline-deployer
    namespace: kubeflow-by-doing
roleRef:
  kind: Role
  name: model-server-deployer
  apiGroup: rbac.authorization.k8s.io
```

Apply:

```bash
kubectl apply -f manifests/model-server/rbac.yaml
```

## Add `deploy_model.py`

Create `components/deploy_model.py`:

```python
from __future__ import annotations

from kfp import dsl


@dsl.component(
    base_image="python:3.12-slim",
    packages_to_install=["kubernetes"],
)
def deploy_model(
    model_uri: str,
    serve_image: str = "kubeflow-by-doing/serve:local",
    namespace: str = "kubeflow-by-doing",
    configmap_name: str = "model-server-config",
    deployment_name: str = "model-server",
) -> str:
    from datetime import datetime, timezone

    from kubernetes import client, config

    config.load_incluster_config()

    core_v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    configmap = core_v1.read_namespaced_config_map(
        name=configmap_name,
        namespace=namespace,
    )
    data = dict(configmap.data or {})
    data["KBD_MODEL_S3_URI"] = model_uri

    core_v1.patch_namespaced_config_map(
        name=configmap_name,
        namespace=namespace,
        body={"data": data},
    )

    restarted_at = datetime.now(timezone.utc).isoformat()
    apps_v1.patch_namespaced_deployment(
        name=deployment_name,
        namespace=namespace,
        body={
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubeflow-by-doing/restarted-at": restarted_at,
                            "kubeflow-by-doing/model-uri": model_uri,
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "server",
                                "image": serve_image,
                            }
                        ]
                    },
                }
            }
        },
    )

    return model_uri
```

## Add `smoke_test_model.py`

Create `components/smoke_test_model.py`:

```python
from __future__ import annotations

from kfp import dsl


@dsl.component(base_image="python:3.12-slim")
def smoke_test_model(
    endpoint: str = "http://model-server.kubeflow-by-doing.svc.cluster.local:8000/predict",
    image_size: int = 16,
) -> None:
    import json
    import urllib.request

    pixels = [[0.75 for _ in range(image_size)] for _ in range(image_size)]
    payload = json.dumps({"pixels": pixels}).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")

    parsed = json.loads(body)

    if "class_id" not in parsed:
        raise RuntimeError(f"invalid prediction response: {parsed}")

    print(parsed)
```

## Configure the Pipeline Task Service Account

Depending on your KFP version, use the Kubernetes extension helper to set the task service account.

Target intent:

```python
from kfp import kubernetes

deploy_task = deploy_model(model_uri=model_uri, serve_image=serve_image)
kubernetes.set_service_account_name(deploy_task, "pipeline-deployer")
```

If the helper differs in your KFP version, Codex should adapt this.

## Update the Pipeline

Update `pipelines/image_classification_pipeline.py`.

Inside the successful promotion branch, add:

```python
deploy_task = deploy_model(model_uri=model_uri, serve_image=serve_image)
smoke_test_model().after(deploy_task)
```

The successful branch should now look like:

```text
promote_model
  ↓
write_lineage
  ↓
deploy_model
  ↓
smoke_test_model
```

A good default is to make deployment opt-in:

```python
deploy_after_promotion: bool = False
```

This avoids surprising redeployments during experiments.

## Recompile the Pipeline

```bash
uv run python pipelines/image_classification_pipeline.py
```

## Run with Deployment Enabled

In the KFP UI, run with:

```text
run_id: serve-kfp-001
min_accuracy: 0.5
deploy_after_promotion: true
```

The exact parameter list depends on your final pipeline implementation.

## Watch the Deployment

```bash
kubectl -n kubeflow-by-doing rollout status deployment/model-server --timeout=120s
kubectl -n kubeflow-by-doing get pods -l app.kubernetes.io/name=model-server
```

## Smoke Test Manually

```bash
kubectl -n kubeflow-by-doing port-forward svc/model-server 8000:8000
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

## Common Problems

### Deploy component cannot access Kubernetes API

Check the task service account and RBAC.

Inspect the failed pod logs and events.

### ConfigMap changes but server still serves old model

A ConfigMap update alone does not restart an existing pod.

The deploy component must restart the Deployment by patching the pod template annotation.

### Smoke test runs too early

Make the smoke test depend on the deploy task. If needed, add a wait loop to `smoke_test_model`.

### Deployment should not happen on every experiment

Add a `deploy_after_promotion` parameter and default it to `false`.

## Acceptance Criteria

You are done when:

- RBAC manifest exists
- `deploy_model.py` exists
- `smoke_test_model.py` exists
- the pipeline can patch the model server ConfigMap
- the pipeline can restart the model server Deployment
- the smoke test succeeds after deployment
- deployment can be disabled by default

## References

- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [Kubernetes Python client](https://github.com/kubernetes-client/python)
- [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)

## Next Step

Continue with [KServe Preview](05-kserve-preview.md).
