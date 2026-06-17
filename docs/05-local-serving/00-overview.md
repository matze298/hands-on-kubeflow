# Local Serving

Chapter 4 made the training workflow durable and traceable.

Chapter 5 turns a promoted model into something callable.

## Prerequisites

Before starting or resuming this chapter, make sure:

- the `kubeflow-gpu` `minikube` profile is running from [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md)
- standalone Kubeflow Pipelines is installed and reachable from [Install Kubeflow Pipelines](../02-kubeflow-pipelines/01-install-kfp.md)
- MinIO is running and the `kubeflow-by-doing` bucket exists from [Install Local Object Storage](../04-artifacts-and-tracking/01-install-minio.md)
- MLflow is running if you want experiment tracking in the serving path, from [Add Experiment Tracking](../04-artifacts-and-tracking/03-add-mlflow.md)
- a promoted model artifact exists from the Chapter 4 pipeline work in [Trace Lineage](../04-artifacts-and-tracking/04-trace-lineage.md)

The goal is to move from:

```text
trained model artifact
```

to:

```text
local HTTP prediction endpoint
  ↓
containerized model server
  ↓
Kubernetes Deployment and Service
  ↓
Kubeflow-triggered smoke test
```

## What You Will Build

You will create the following target files during this chapter:

```text
src/kubeflow_by_doing/
├── serve.py
└── client.py

Dockerfile.serve

manifests/model-server/
├── configmap.yaml
├── deployment.yaml
├── service.yaml
└── rbac.yaml

components/
├── deploy_model.py
└── smoke_test_model.py

pipelines/
└── image_classification_pipeline.py
```

## Why This Matters

Training is not the end of an ML workflow.

A useful platform needs a path from:

```text
model passes evaluation
```

to:

```text
model can answer requests
```

This chapter uses a deliberately simple serving setup:

- FastAPI for the model server
- a normal Kubernetes `Deployment`
- a normal Kubernetes `Service`
- port forwarding for local access
- a simple Kubeflow smoke-test component

KServe is introduced only as a preview. The core path stays transparent and debuggable.

This chapter assumes the default `minikube` local Kubernetes path. If you are still on the starter `kind` cluster, keep the serving workflow but use the `kind` image-loading commands where noted.

## Serving Architecture

```text
MinIO
  └── s3://kubeflow-by-doing/runs/<run_id>/models/model.pt
        ↓
FastAPI model server
        ↓
Kubernetes Deployment
        ↓
Kubernetes Service
        ↓
curl / Python client / KFP smoke test
```

## Local-First Scope

This chapter does not add:

- public ingress
- TLS
- autoscaling
- canary rollouts
- KServe production serving
- authentication
- model registry integration

Those are later expansion topics.

The goal here is to make model serving concrete.

## Chapter Files

```text
docs/05-local-serving/
├── 00-overview.md
├── 01-fastapi-model-server.md
├── 02-containerize-serving.md
├── 03-deploy-to-kubernetes.md
├── 04-connect-pipeline-to-serving.md
└── 05-kserve-preview.md
```

## Acceptance Criteria

You are done with Chapter 5 when:

- a FastAPI model server can load a trained model
- `/healthz` returns a healthy response
- `/predict` returns a class prediction
- the serving image can be built locally
- the serving image can be loaded into the default `minikube` cluster, or into `kind` as the fallback path
- the model server runs inside Kubernetes
- the service can be reached through port forwarding
- a pipeline promotion path can update or smoke-test the served model
- you understand where KServe fits later

## Next Step

Start with [FastAPI Model Server](01-fastapi-model-server.md).
