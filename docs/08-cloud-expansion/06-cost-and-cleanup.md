# Cost and Cleanup

This page defines a provider-neutral cost and cleanup checklist.

## What You Will Build

You will create:

```text
infra/cloud/cleanup/cleanup-checklist.md
infra/cloud/cleanup/delete-object-prefixes.py
```

## Why This Matters

Cloud resources can keep costing money after the tutorial is over.

Common leftover resources:

- Kubernetes clusters
- node pools
- GPU node pools
- load balancers
- public IPs
- persistent volumes
- object storage buckets
- registry images
- NAT gateways
- managed databases
- log storage

## Create Cleanup Folder

```bash
mkdir -p infra/cloud/cleanup
```

## Create `cleanup-checklist.md`

Create `infra/cloud/cleanup/cleanup-checklist.md`:

```markdown
# Generic Cloud Cleanup Checklist

Use this checklist for any managed Kubernetes provider.

## 1. Stop Local Port-Forwards

Stop terminals running:

```bash
kubectl port-forward ...
```

## 2. Delete Tutorial Namespaces

```bash
kubectl delete namespace kubeflow-by-doing --ignore-not-found
kubectl delete namespace kubeflow --ignore-not-found
```

## 3. Check Persistent Volumes

```bash
kubectl get pv
kubectl get pvc -A
```

Delete provider volumes that are no longer needed.

## 4. Check Load Balancers

```bash
kubectl get svc -A
```

Delete `LoadBalancer` services if they exist.

## 5. Delete GPU Node Pools

Delete or scale down GPU node pools first.

GPU nodes are usually the highest-cost resource.

## 6. Delete CPU Node Pools or Cluster

If the tutorial is complete, delete the managed Kubernetes cluster.

## 7. Delete Object Storage Objects

Delete tutorial prefixes:

```text
runs/
reports/
predictions/
lineage/
mlflow-artifacts/
kfp/
```

Only delete the bucket if it is not shared.

## 8. Delete Registry Images

Delete tutorial image tags:

```text
kubeflow-by-doing-train
kubeflow-by-doing-train-gpu
kubeflow-by-doing-serve
```

## 9. Delete IAM / Service Accounts / Access Keys

Delete any tutorial-only credentials.

## 10. Delete Local Secrets

```bash
rm -f .env.cloud
rm -rf .kube/
rm -f infra/cloud/secrets/*.generated.yaml
```

## 11. Verify in Provider Console

Check billing/resource pages for:

- clusters
- node pools
- disks
- load balancers
- buckets
- registries
- public IPs
- databases
```

## Object Prefix Cleanup Script

Create `infra/cloud/cleanup/delete-object-prefixes.py`:

```python
from __future__ import annotations

import os

import boto3
from botocore.client import Config


PREFIXES = [
    "runs/",
    "reports/",
    "predictions/",
    "lineage/",
    "mlflow-artifacts/",
    "kfp/",
]


def main() -> None:
    endpoint_url = os.environ["KBD_S3_ENDPOINT_URL"]
    bucket = os.environ["KBD_ARTIFACT_BUCKET"]

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_DEFAULT_REGION"),
        config=Config(signature_version="s3v4"),
    )

    for prefix in PREFIXES:
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        objects = [{"Key": item["Key"]} for item in response.get("Contents", [])]

        if not objects:
            print(f"no objects under s3://{bucket}/{prefix}")
            continue

        client.delete_objects(Bucket=bucket, Delete={"Objects": objects})
        print(f"deleted {len(objects)} objects under s3://{bucket}/{prefix}")


if __name__ == "__main__":
    main()
```

Run only when you are sure:

```bash
source .env.cloud
uv run python infra/cloud/cleanup/delete-object-prefixes.py
```

## Cost Planning Before Creation

Before creating cloud resources, write down:

```text
cluster name:
region:
CPU node count:
GPU node count:
object storage bucket:
registry:
expected cleanup date:
```

Add it to your local `.env.cloud` or a non-committed notes file.

## Common Problems

### Namespace deletion hangs

Check finalizers and remaining resources:

```bash
kubectl get all -n kubeflow-by-doing
kubectl get pvc -n kubeflow-by-doing
```

### Load balancer remains after namespace deletion

Check provider console. Some cloud resources can outlive Kubernetes objects temporarily or due to failed cleanup.

### Object storage bucket cannot be deleted

The bucket is not empty or versioning is enabled.

Delete object versions according to provider docs.

## Acceptance Criteria

You are done when:

- cleanup checklist exists
- object prefix cleanup script exists
- GPU cleanup is listed before cluster cleanup
- registry cleanup is included
- object storage cleanup is included
- local secrets cleanup is included
- provider console verification is included

## References

- [Kubernetes garbage collection](https://kubernetes.io/docs/concepts/architecture/garbage-collection/)
- [Kubernetes Services LoadBalancer](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)
- [Kubernetes persistent volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

## Next Step

Continue with [Provider Checklist](07-provider-checklist.md).
