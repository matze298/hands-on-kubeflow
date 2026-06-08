# Cost Control and Cleanup

This page makes cleanup explicit.

Cloud tutorials should never leave expensive resources running by accident.

## What You Will Build

You will create:

```text
infra/stackit/cleanup.md
```

This file documents exactly what to delete or scale down.

## Why This Matters

Local clusters are cheap to forget.

Cloud clusters are not.

The expensive parts are usually:

- Kubernetes worker nodes
- GPU node pools
- load balancers
- persistent volumes
- object storage
- container registry storage
- running MLflow or serving workloads

## Create `infra/stackit/cleanup.md`

```markdown
# STACKIT Cleanup

Use this checklist after the STACKIT chapter.

## 1. Stop Port-Forwards

Stop any local `kubectl port-forward` processes.

## 2. Delete Tutorial Workloads

```bash
kubectl delete pod stackit-gpu-check -n kubeflow-by-doing --ignore-not-found
```

## 3. Delete Tutorial Namespaces

```bash
kubectl delete namespace kubeflow-by-doing --ignore-not-found
kubectl delete namespace kubeflow --ignore-not-found
```

## 4. Scale Down or Delete GPU Node Pool

Use the STACKIT Portal or CLI to scale the GPU node pool to zero or delete it.

## 5. Delete SKE Cluster

Use the STACKIT Portal or CLI to delete `kbd-ske` if it is no longer needed.

## 6. Delete Object Storage Objects

Delete tutorial objects under:

```text
s3://kubeflow-by-doing/datasets/
s3://kubeflow-by-doing/models/
s3://kubeflow-by-doing/metrics/
s3://kubeflow-by-doing/reports/
s3://kubeflow-by-doing/predictions/
s3://kubeflow-by-doing/lineage/
s3://kubeflow-by-doing/runs/
s3://kubeflow-by-doing/mlflow-artifacts/
```

Then delete the bucket if it is no longer needed.

## 7. Delete Registry Images

Delete tutorial image tags:

```text
kubeflow-by-doing-train:stackit
kubeflow-by-doing-train:gpu-stackit
kubeflow-by-doing-serve:stackit
```

## 8. Delete Local Secrets

```bash
rm -f .env.stackit
rm -rf .kube/
```

## 9. Verify in STACKIT Portal

Check that no tutorial resources remain:

- SKE clusters
- GPU node pools
- load balancers
- volumes
- object storage buckets
- registry images
```

## Kubernetes Cleanup Commands

If the cluster is still available:

```bash
kubectl delete namespace kubeflow-by-doing --ignore-not-found
kubectl delete namespace kubeflow --ignore-not-found
```

Check remaining resources:

```bash
kubectl get all -A
kubectl get pvc -A
kubectl get svc -A
```

## Object Storage Cleanup Script

Create `scripts/stackit-delete-tutorial-objects.py`:

```python
from __future__ import annotations

import os

import boto3
from botocore.client import Config


PREFIXES = [
    "datasets/",
    "models/",
    "metrics/",
    "reports/",
    "predictions/",
    "lineage/",
    "runs/",
    "mlflow-artifacts/",
]


def main() -> None:
    endpoint_url = os.environ["KBD_S3_ENDPOINT_URL"]
    bucket = os.environ["KBD_ARTIFACT_BUCKET"]

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "eu01"),
        config=Config(signature_version="s3v4"),
    )

    for prefix in PREFIXES:
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objects = [{"Key": item["Key"]} for item in response.get("Contents", [])]

        if objects:
            client.delete_objects(Bucket=bucket, Delete={"Objects": objects})
            print(f"deleted {len(objects)} objects under s3://{bucket}/{prefix}")
        else:
            print(f"no objects under s3://{bucket}/{prefix}")


if __name__ == "__main__":
    main()
```

Run only when you are sure:

```bash
source .env.stackit
uv run python scripts/stackit-delete-tutorial-objects.py
```

## Cost-Control Defaults

For tutorial use:

```text
small CPU node pool
no public ingress unless needed
GPU node pool only during GPU exercise
port-forward instead of LoadBalancer where possible
delete cluster after chapter
```

## What Not to Delete Accidentally

Before deleting buckets or registry images, check whether they are shared with other work.

Use tutorial-specific names:

```text
kbd-ske
kubeflow-by-doing
kubeflow-by-doing-train
kubeflow-by-doing-serve
```

## Acceptance Criteria

You are done when:

- cleanup checklist exists
- GPU node pool is deleted or scaled down
- tutorial namespaces are deleted if no longer needed
- object storage tutorial prefixes are removed if no longer needed
- registry images are removed if no longer needed
- SKE cluster is deleted if the tutorial is complete
- `.env.stackit` and local kubeconfig are removed or secured

## References

- [STACKIT Kubernetes Engine documentation](https://docs.stackit.cloud/products/runtime/kubernetes-engine/)
- [STACKIT Object Storage documentation](https://docs.stackit.cloud/products/storage/object-storage/)
- [STACKIT Container Registry documentation](https://docs.stackit.cloud/products/developer-platform/container-registry/)

## Next Step

Continue with Chapter 8: Generic Cloud Expansion.
