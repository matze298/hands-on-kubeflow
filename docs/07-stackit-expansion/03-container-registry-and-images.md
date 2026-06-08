# Container Registry and Images

This page moves the tutorial images from local-only images to registry-hosted images that SKE can pull.

## What You Will Build

You will create:

```text
scripts/stackit-build-and-push.sh
infra/stackit/container-registry-secret.yaml
```

## Why This Matters

In local kind or MicroK8s, we can import images directly.

In SKE, worker nodes need to pull images from a registry.

That means the image path must change from:

```text
kubeflow-by-doing/train:local
```

to something like:

```text
<registry-host>/<namespace>/kubeflow-by-doing-train:stackit
```

## Create `scripts/stackit-build-and-push.sh`

```bash
mkdir -p scripts
```

Create `scripts/stackit-build-and-push.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${KBD_TRAIN_IMAGE:?Set KBD_TRAIN_IMAGE}"
: "${KBD_SERVE_IMAGE:?Set KBD_SERVE_IMAGE}"

echo "Building training image: ${KBD_TRAIN_IMAGE}"
docker build -t "${KBD_TRAIN_IMAGE}" .

echo "Building serving image: ${KBD_SERVE_IMAGE}"
docker build -f Dockerfile.serve -t "${KBD_SERVE_IMAGE}" .

echo "Pushing training image"
docker push "${KBD_TRAIN_IMAGE}"

echo "Pushing serving image"
docker push "${KBD_SERVE_IMAGE}"

echo "Done"
```

Make it executable:

```bash
chmod +x scripts/stackit-build-and-push.sh
```

## Log in to the Registry

Use your registry host and credentials.

For Docker-compatible registries, the shape is:

```bash
docker login "$KBD_REGISTRY_HOST"
```

For STACKIT Container Registry, create registry credentials or a robot account according to your project policy.

## Build and Push

```bash
source .env.stackit
./scripts/stackit-build-and-push.sh
```

Verify:

```bash
docker pull "$KBD_TRAIN_IMAGE"
docker pull "$KBD_SERVE_IMAGE"
```

## Create an Image Pull Secret

If your registry is private, create `infra/stackit/container-registry-secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kbd-registry-credentials
  namespace: kubeflow-by-doing
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config-json>
```

For a quicker local command-based creation:

```bash
kubectl -n kubeflow-by-doing create secret docker-registry kbd-registry-credentials \
  --docker-server="$KBD_REGISTRY_HOST" \
  --docker-username="<registry-username>" \
  --docker-password="<registry-password>" \
  --docker-email="<email>" \
  --dry-run=client -o yaml > infra/stackit/container-registry-secret.yaml
```

Apply:

```bash
kubectl apply -f infra/stackit/container-registry-secret.yaml
```

## Use the Pull Secret in Components

For KFP tasks, the exact helper depends on the KFP SDK version.

Target intent:

```python
from kfp import kubernetes

kubernetes.set_image_pull_secrets(
    task,
    ["kbd-registry-credentials"],
)
```

If your SDK uses a different method, adapt during Codex hardening.

## Update Pipeline Image Parameters

Run cloud pipeline with:

```text
cpu_image: <KBD_TRAIN_IMAGE>
gpu_image: <KBD_TRAIN_IMAGE or GPU image if available>
```

For serving, update the Kubernetes Deployment image:

```yaml
image: <KBD_SERVE_IMAGE>
```

Do not leave local-only image names in SKE manifests.

## Smoke Test Image Pull

Create `infra/stackit/image-pull-smoke.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: image-pull-smoke
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  imagePullSecrets:
    - name: kbd-registry-credentials
  containers:
    - name: train
      image: <replace-with-KBD_TRAIN_IMAGE>
      args: ["--help"]
```

Apply after replacing the image:

```bash
kubectl apply -f infra/stackit/image-pull-smoke.yaml
kubectl -n kubeflow-by-doing logs pod/image-pull-smoke
kubectl -n kubeflow-by-doing delete pod image-pull-smoke --ignore-not-found
```

## Common Problems

### `ImagePullBackOff`

Inspect:

```bash
kubectl -n kubeflow-by-doing describe pod image-pull-smoke
```

Check:

- image name
- tag
- registry host
- pull secret
- registry permissions

### Pipeline still uses local images

Search:

```bash
grep -R "kubeflow-by-doing/train:local\\|serve:local" -n pipelines manifests docs || true
```

### Registry credentials are committed

Do not commit generated credentials with real secrets.

Prefer sealed secrets, external secret managers, or CI-provided credentials for real projects.

## Acceptance Criteria

You are done when:

- training image is pushed to a registry
- serving image is pushed to a registry
- SKE can pull the training image
- image pull secret exists if needed
- pipeline image parameters use registry-hosted image names
- no cloud manifest depends on local-only image imports

## References

- [STACKIT Container Registry documentation](https://docs.stackit.cloud/products/developer-platform/container-registry/)
- [Create your first STACKIT Container Registry](https://docs.stackit.cloud/products/developer-platform/container-registry/getting-started/getting-started-with-container-registry/)
- [Kubernetes image pull secrets](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)

## Next Step

Continue with [Object Storage and Secrets](04-object-storage-and-secrets.md).
