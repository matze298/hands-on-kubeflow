# Cloud Mapping

This page maps the capstone to STACKIT or another managed Kubernetes provider.

## What Changes

The capstone pipeline should remain the same.

Provider overlays change:

```text
KUBECONFIG
image names
object storage endpoint
object storage credentials
registry credentials
pipeline root
GPU node pool availability
serving exposure strategy
cleanup plan
```

## Local to STACKIT Mapping

| Capstone concern | Local | STACKIT |
|---|---|---|
| Kubernetes | MicroK8s / kind | SKE |
| Images | local import | container registry |
| Object storage | MinIO | STACKIT Object Storage |
| KFP | local install | SKE install |
| MLflow | local in-cluster | SKE in-cluster or managed alternative |
| GPU | local NVIDIA | GPU node pool |
| Serving | ClusterIP + port-forward | ClusterIP + port-forward first |
| Cleanup | delete local resources | delete SKE resources and cloud artifacts |

## Local to Generic Cloud Mapping

| Capstone concern | Generic provider variable |
|---|---|
| Kubernetes | `KUBECONFIG` |
| CPU image | `KBD_TRAIN_IMAGE` |
| GPU image | `KBD_GPU_TRAIN_IMAGE` |
| Serving image | `KBD_SERVE_IMAGE` |
| Object storage endpoint | `KBD_S3_ENDPOINT_URL` |
| Bucket | `KBD_ARTIFACT_BUCKET` |
| Credentials | `artifact-store-credentials` |
| GPU | `accelerator`, `gpu_count`, node pool |
| Deployment | `deploy_after_promotion` |

## Provider-Neutral Run Parameters

Use the same capstone parameters:

```text
run_id
dataset_uri
accelerator
gpu_count
cpu_image
gpu_image
serve_image
artifact_bucket
min_accuracy
deploy_after_promotion
git_sha
n_train
n_val
image_size
n_classes
epochs
learning_rate
batch_size
```

## STACKIT Example

```text
run_id: capstone-stackit-001
dataset_uri: synthetic://tiny-image-classification
accelerator: cpu
gpu_count: 0
cpu_image: <STACKIT registry training image>
gpu_image: <STACKIT registry GPU image>
serve_image: <STACKIT registry serving image>
artifact_bucket: <STACKIT object storage bucket>
min_accuracy: 0.5
deploy_after_promotion: false
git_sha: <git sha>
```

## Generic Cloud Example

```text
run_id: capstone-cloud-001
dataset_uri: synthetic://tiny-image-classification
accelerator: cpu
gpu_count: 0
cpu_image: <provider registry training image>
gpu_image: <provider registry GPU image>
serve_image: <provider registry serving image>
artifact_bucket: <provider object storage bucket>
min_accuracy: 0.5
deploy_after_promotion: false
git_sha: <git sha>
```

## What Not to Change

Do not fork the capstone pipeline per provider unless there is a strong reason.

Avoid:

```text
capstone_pipeline_aws.py
capstone_pipeline_azure.py
capstone_pipeline_stackit.py
```

Prefer:

```text
same pipeline
different environment overlay
different secrets
different image parameters
```

## Cloud Preflight

Before running capstone in a cloud provider:

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get namespace kubeflow
kubectl get namespace kubeflow-by-doing
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
```

Check image pull:

```bash
kubectl apply -f infra/cloud/checks/image-pull-check.generated.yaml
kubectl -n kubeflow-by-doing logs pod/image-pull-check
kubectl -n kubeflow-by-doing delete pod image-pull-check --ignore-not-found
```

Check object storage:

```bash
uv run python infra/cloud/checks/object-storage-check.py
```

## Cloud Acceptance Criteria

A cloud capstone mapping is successful when:

- same pipeline compiles
- cloud images are passed as parameters
- object storage secret points to cloud storage
- CPU pipeline run succeeds
- artifacts appear in cloud object storage
- serving works privately through port-forwarding
- GPU path is either validated or explicitly deferred
- cleanup plan exists

## Cleanup Reminder

Before creating cloud resources, define:

```text
cluster:
node pools:
GPU node pool:
bucket:
registry:
cleanup date:
cleanup owner:
```

After running:

```text
delete namespaces
delete or scale GPU node pool
delete cluster if disposable
delete tutorial object prefixes
delete registry images
delete local secrets
```

## Final Course Completion Criteria

You are done with the tutorial when:

- local capstone succeeds
- artifacts are durable
- metrics control promotion
- a promoted model can be served
- endpoint smoke test succeeds
- CI can compile the pipeline
- cloud mapping is understood
- cleanup is documented

## References

- [STACKIT Kubernetes Engine documentation](https://docs.stackit.cloud/products/runtime/kubernetes-engine/)
- [STACKIT Object Storage documentation](https://docs.stackit.cloud/products/storage/object-storage/)
- [Kubeflow Pipelines documentation](https://www.kubeflow.org/docs/components/pipelines/)
- [Kubernetes image pull secrets](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)

## Congratulations

You now have a complete local-first Kubeflow workflow:

```text
code
  ↓
container
  ↓
Kubeflow pipeline
  ↓
artifact storage
  ↓
tracking and lineage
  ↓
promotion
  ↓
serving
  ↓
smoke test
  ↓
cloud mapping
```

## Next Step

Continue with [Conclusion and Future Reading](../11-conclusion/00-overview.md).
