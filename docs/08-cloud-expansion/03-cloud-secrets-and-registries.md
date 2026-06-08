# Cloud Secrets and Registries

This page generalizes image pull and object storage secrets across providers.

## What You Will Build

You will create:

```text
infra/cloud/secrets/
├── artifact-store-secret.template.yaml
└── image-pull-secret.md

infra/cloud/checks/
└── image-pull-check.yaml
```

## Why This Matters

Cloud failures often happen before your code starts:

```text
ImagePullBackOff
AccessDenied
NoCredentialsError
Forbidden
```

A provider-neutral pipeline still needs provider-specific authentication.

## Create Secret Folder

```bash
mkdir -p infra/cloud/secrets
mkdir -p infra/cloud/checks
```

## Artifact Store Secret Template

Create `infra/cloud/secrets/artifact-store-secret.template.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: artifact-store-credentials
  namespace: kubeflow-by-doing
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
  AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
  AWS_DEFAULT_REGION: "${AWS_DEFAULT_REGION}"
  KBD_S3_ENDPOINT_URL: "${KBD_S3_ENDPOINT_URL}"
  KBD_ARTIFACT_BUCKET: "${KBD_ARTIFACT_BUCKET}"
  MLFLOW_S3_ENDPOINT_URL: "${MLFLOW_S3_ENDPOINT_URL}"
  MLFLOW_TRACKING_URI: "${MLFLOW_TRACKING_URI}"
  MLFLOW_EXPERIMENT_NAME: "${MLFLOW_EXPERIMENT_NAME}"
```

Generate a local filled secret:

```bash
source .env.cloud

envsubst < infra/cloud/secrets/artifact-store-secret.template.yaml \
  > infra/cloud/secrets/artifact-store-secret.generated.yaml
```

!!! warning

    The generated file contains secrets. Do not commit it.

Apply:

```bash
kubectl apply -f infra/cloud/secrets/artifact-store-secret.generated.yaml
```

## Image Pull Secret

Create `infra/cloud/secrets/image-pull-secret.md`:

```markdown
# Image Pull Secret

If the registry is private, create an image pull secret.

```bash
kubectl -n kubeflow-by-doing create secret docker-registry kbd-registry-credentials \
  --docker-server="$KBD_REGISTRY" \
  --docker-username="<registry-username>" \
  --docker-password="<registry-password>" \
  --docker-email="<email>" \
  --dry-run=client -o yaml > infra/cloud/secrets/image-pull-secret.generated.yaml

kubectl apply -f infra/cloud/secrets/image-pull-secret.generated.yaml
```

Do not commit generated secrets.

If your provider uses workload identity or node-level registry integration, document that instead of using a static pull secret.
```

## Image Pull Smoke Test

Create `infra/cloud/checks/image-pull-check.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: image-pull-check
  namespace: kubeflow-by-doing
spec:
  restartPolicy: Never
  imagePullSecrets:
    - name: kbd-registry-credentials
  containers:
    - name: train
      image: REPLACE_WITH_TRAIN_IMAGE
      command: ["kbd", "--help"]
```

Replace the image:

```bash
cp infra/cloud/checks/image-pull-check.yaml infra/cloud/checks/image-pull-check.generated.yaml
python - <<'PY'
from pathlib import Path
import os

path = Path("infra/cloud/checks/image-pull-check.generated.yaml")
text = path.read_text(encoding="utf-8")
text = text.replace("REPLACE_WITH_TRAIN_IMAGE", os.environ["KBD_TRAIN_IMAGE"])
path.write_text(text, encoding="utf-8")
PY
```

Apply:

```bash
kubectl apply -f infra/cloud/checks/image-pull-check.generated.yaml
kubectl -n kubeflow-by-doing logs pod/image-pull-check
kubectl -n kubeflow-by-doing delete pod image-pull-check --ignore-not-found
```

## KFP Task Integration

If using image pull secrets in KFP, configure tasks according to your KFP SDK version.

Target intent:

```python
from kfp import kubernetes

kubernetes.set_image_pull_secrets(
    task,
    ["kbd-registry-credentials"],
)
```

If your provider uses node-level identity for registry pulls, you may not need a KFP-level image pull secret.

## Common Provider Patterns

### AWS

Common options:

- ECR with node IAM permissions
- ECR with generated Docker login secret
- IRSA for workload identity where applicable

### Azure

Common options:

- AKS attached to ACR
- image pull secret
- managed identity integration

### Google Cloud

Common options:

- GKE nodes with Artifact Registry access
- workload identity
- image pull secret in special cases

### Generic

Common options:

- Docker registry secret
- public images
- private registry robot account

## Acceptance Criteria

You are done when:

- artifact store secret template exists
- image pull secret instructions exist
- a generated artifact secret is applied locally
- image pull smoke pod succeeds
- KFP task image pull strategy is documented
- no generated real secret is committed

## References

- [Kubernetes image pull secrets](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)

## Next Step

Continue with [Object Storage Abstraction](04-object-storage-abstraction.md).
