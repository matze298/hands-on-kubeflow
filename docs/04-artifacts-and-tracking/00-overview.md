# Artifacts and Tracking

Chapter 3 produced a local training workflow and ran it through Kubeflow.

Chapter 4 makes the workflow more platform-like by adding:

- local S3-compatible object storage with MinIO
- a portable artifact layout
- MLflow experiment tracking
- explicit lineage records

The goal is to answer the question:

```text
Which data, code, image, parameters, and run produced this model?
```

## What You Will Build

You will create the following target files during this chapter:

```text
infra/minio/
├── namespace.yaml
├── secret.yaml
├── pvc.yaml
├── deployment.yaml
├── service.yaml
└── app-secret.yaml

infra/mlflow/
├── deployment.yaml
└── service.yaml

src/kubeflow_by_doing/
├── storage.py
├── tracking.py
└── lineage.py

components/
├── train_model.py
├── evaluate_model.py
└── write_lineage.py

pipelines/
└── image_classification_pipeline.py
```

## Why This Matters

Kubernetes pods are temporary.

If a training pod writes `model.pt` only to its local filesystem, the artifact disappears when the pod is gone.

A practical ML platform needs durable and inspectable outputs:

```text
datasets
models
metrics
reports
predictions
lineage records
```

Kubeflow tracks pipeline structure and artifacts. Object storage gives us durable files. MLflow gives us familiar experiment tracking. A lineage record connects the pieces.

From this chapter onward, the tutorial assumes the default `minikube` local Kubernetes path. The `kind` starter cluster remains available for the early Kubernetes chapters, but the artifact and tracking workflow is written for the GPU-capable `minikube` setup.

## Target Architecture

```text
Kubeflow Pipeline
├── train_model
│   ├── writes model artifact to KFP artifact path
│   ├── uploads model artifact to MinIO
│   └── logs params/metrics/artifacts to MLflow
├── evaluate_model
│   ├── reads model
│   ├── writes metrics
│   ├── uploads metrics to MinIO
│   └── logs metrics to MLflow
└── write_lineage
    └── records Git SHA, image tag, artifact URIs, KFP run info, MLflow run info
```

## Artifact Layout

The portable target layout is:

```text
s3://kubeflow-by-doing/
├── datasets/
├── models/
├── metrics/
├── reports/
├── predictions/
└── lineage/
```

Locally, this is backed by MinIO. In a later STACKIT or cloud chapter, the same layout can move to cloud object storage.

## Chapter Files

```text
docs/04-artifacts-and-tracking/
├── 00-overview.md
├── 01-install-minio.md
├── 02-artifact-layout.md
├── 03-add-mlflow.md
└── 04-trace-lineage.md
```

## Acceptance Criteria

You are done with Chapter 4 when:

- MinIO runs locally in Kubernetes
- the bucket `kubeflow-by-doing` exists
- MinIO credentials are available to pipeline pods through Kubernetes Secrets
- MLflow runs locally in Kubernetes
- training and evaluation can log to MLflow
- model and metrics artifacts are uploaded to MinIO
- lineage records include Git SHA, image tag, dataset URI, model URI, metrics URI, KFP run ID, and MLflow run information where available
- the final pipeline run produces durable artifacts outside the pod filesystem

## Next Step

Start with [Install Local Object Storage](01-install-minio.md).
