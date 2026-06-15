# STACKIT Architecture

This page maps the local tutorial architecture to STACKIT.

## What You Will Define

Create:

```text
infra/stackit/README.md
infra/stackit/env.example
```

These files document the cloud environment and keep commands explicit.

## Why This Matters

Cloud migration goes wrong when hidden assumptions stay local.

Examples:

- image exists only in local Docker
- `localhost:9000` points to MinIO
- Kubernetes pod cannot reach local services
- credentials exist only in your shell
- GPU is visible locally but not in the cloud cluster

This page turns those assumptions into explicit configuration.

## Local to STACKIT Mapping

| Concern | Local | STACKIT |
|---|---|---|
| Kubernetes | minikube / kind | STACKIT Kubernetes Engine |
| Image distribution | local image loading | STACKIT Container Registry or another OCI registry |
| Object storage | MinIO | STACKIT Object Storage |
| Artifact URI | `s3://kubeflow-by-doing/...` | same layout, different endpoint/credentials |
| GPU | local NVIDIA GPU | GPU node pool |
| KFP UI | port-forward | port-forward first |
| Serving | ClusterIP + port-forward | ClusterIP + port-forward first |
| Cleanup | delete cluster | delete SKE cluster, buckets, registry images, credentials |

## Create `infra/stackit/README.md`

```markdown
# STACKIT Expansion

This folder contains the STACKIT-specific configuration for the Kubeflow by Doing tutorial.

The local workflow remains the source architecture. STACKIT replaces the infrastructure boundaries:

- minikube/kind -> STACKIT Kubernetes Engine
- local image loading -> container registry
- MinIO -> STACKIT Object Storage
- local GPU -> SKE GPU node pool

## Required STACKIT Resources

- STACKIT project
- SKE cluster
- object storage bucket
- object storage access key and secret key
- container registry or another OCI registry reachable by SKE
- optional GPU node pool

## Local Environment File

Copy:

```bash
cp infra/stackit/env.example .env.stackit
```

Then fill in values.

Do not commit `.env.stackit`.
```

## Create `infra/stackit/env.example`

```bash
# STACKIT project and cluster
export STACKIT_PROJECT_ID="<your-stackit-project-id>"
export STACKIT_CLUSTER_NAME="kbd-ske"
export STACKIT_REGION="<your-stackit-region>"

# Kubernetes
export KUBECONFIG="$PWD/.kube/stackit-kubeconfig.yaml"

# Container registry
export KBD_REGISTRY_HOST="<registry-host>"
export KBD_REGISTRY_NAMESPACE="<registry-namespace-or-project>"
export KBD_TRAIN_IMAGE="$KBD_REGISTRY_HOST/$KBD_REGISTRY_NAMESPACE/kubeflow-by-doing-train:stackit"
export KBD_SERVE_IMAGE="$KBD_REGISTRY_HOST/$KBD_REGISTRY_NAMESPACE/kubeflow-by-doing-serve:stackit"

# Object storage
export KBD_ARTIFACT_BUCKET="kubeflow-by-doing"
export KBD_S3_ENDPOINT_URL="<stackit-object-storage-s3-endpoint>"
export AWS_ACCESS_KEY_ID="<object-storage-access-key-id>"
export AWS_SECRET_ACCESS_KEY="<object-storage-secret-access-key>"
export AWS_DEFAULT_REGION="eu01"

# MLflow and KFP
export MLFLOW_EXPERIMENT_NAME="kubeflow-by-doing-stackit"
```

!!! warning

    `.env.stackit` contains credentials. Add it to `.gitignore` if it is not already ignored.

## Add `.gitignore` Entries

If needed, add:

```gitignore
.env.stackit
.kube/
```

## Source the Environment

```bash
cp infra/stackit/env.example .env.stackit
# edit .env.stackit
source .env.stackit
```

Verify:

```bash
echo "$STACKIT_PROJECT_ID"
echo "$KBD_TRAIN_IMAGE"
echo "$KBD_S3_ENDPOINT_URL"
```

## Keep the Artifact Layout Stable

Do not change the logical artifact layout:

```text
s3://kubeflow-by-doing/runs/<run_id>/
├── models/
├── metrics/
├── reports/
├── predictions/
└── lineage/
```

Only these change:

```text
endpoint URL
credentials
bucket provider
```

## Common Problems

### Using `localhost` in cloud pods

Cloud pods cannot reach your local MinIO or MLflow.

Replace local endpoints with cluster-reachable or cloud endpoints.

### Hardcoding image names

Do not leave:

```text
kubeflow-by-doing/train:local
```

in cloud pipeline runs.

Use:

```text
$KBD_TRAIN_IMAGE
```

or pass image names as pipeline parameters.

### Committing credentials

Never commit `.env.stackit`, kubeconfigs, or object storage secrets.

## Acceptance Criteria

You are done when:

- `infra/stackit/README.md` exists
- `infra/stackit/env.example` exists
- `.env.stackit` is created locally but not committed
- image names, object storage endpoint, bucket, and project ID are explicit
- you can explain which parts of the local architecture are replaced by STACKIT

## References

- [STACKIT Kubernetes Engine documentation](https://docs.stackit.cloud/products/runtime/kubernetes-engine/)
- [STACKIT Object Storage documentation](https://docs.stackit.cloud/products/storage/object-storage/)
- [STACKIT Container Registry documentation](https://docs.stackit.cloud/products/developer-platform/container-registry/)

## Next Step

Continue with [Create an SKE Cluster](02-create-ske-cluster.md).
