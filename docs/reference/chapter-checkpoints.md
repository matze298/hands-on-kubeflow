# Chapter Checkpoints

Use this page to check whether your local repository and local platform state match the tutorial after each chapter.

The [Verification Matrix](verification-matrix.md) focuses on commands. This page focuses on expected outcomes: files, services, images, artifacts, and decisions.

## 0. Orientation

Expected outcome:

- you understand the local-first course path
- you know that `k3s` is the default local ML/Kubeflow platform
- you know that `kind` is the starter and CPU fallback path
- you can run the docs locally with `uv run mkdocs serve`

Useful checks:

```bash
uv run mkdocs build --strict
```

## 1. Local Kubernetes

Expected outcome:

- local tooling is installed
- `kind` starter cluster can run a simple workload
- `k3s` is available for the ML chapters
- `kubeflow-by-doing` namespace exists
- GPU smoke tests either pass or the CPU fallback status is clear

Expected paths:

```text
infra/k8s/
infra/kind/
infra/k3s/
```

Useful checks:

```bash
kubectl config current-context
kubectl get nodes -o wide
kubectl get namespace kubeflow-by-doing
```

## 2. Kubeflow Pipelines

Expected outcome:

- standalone KFP is installed in the `kubeflow` namespace
- KFP UI is reachable through port-forwarding
- starter pipelines compile into `compiled/`
- a simple run can be inspected in the UI

Expected paths:

```text
pipelines/hello_pipeline.py
pipelines/tiny_ml_pipeline.py
pipelines/submit_hello_pipeline.py
compiled/hello_pipeline.yaml
compiled/tiny_ml_pipeline.yaml
```

Useful checks:

```bash
kubectl get pods -n kubeflow
uv run python pipelines/hello_pipeline.py
uv run python pipelines/tiny_ml_pipeline.py
```

## 3. Local ML Workflow

Expected outcome:

- tutorial ML code lives under `src/kubeflow_by_doing/`
- local train and evaluate commands work
- tests, linting, formatting, and type checks run locally
- CPU training image builds
- training pipeline compiles

Expected paths:

```text
src/kubeflow_by_doing/
components/
pipelines/image_classification_pipeline.py
tests/
Dockerfile
compiled/image_classification_pipeline.yaml
```

Useful checks:

```bash
uv run pytest
uv run ruff check .
uv run ty check
docker build -t kubeflow-by-doing/train:local .
uv run python pipelines/image_classification_pipeline.py
```

## 4. Artifacts and Tracking

Expected outcome:

- MinIO runs in the `minio` namespace
- `artifact-store-credentials` exists in `kubeflow-by-doing`
- local code can upload model, metrics, and lineage objects
- MLflow runs in the tutorial namespace
- artifact layout uses `runs/<run_id>/...`

Expected paths:

```text
infra/minio/
infra/mlflow/
src/kubeflow_by_doing/artifacts.py
src/kubeflow_by_doing/tracking.py
components/write_lineage.py
```

Useful checks:

```bash
kubectl -n minio get pods
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
kubectl -n kubeflow-by-doing get svc mlflow
```

## 5. Local Serving

Expected outcome:

- FastAPI model server works locally
- serving image builds
- Kubernetes `Deployment` and `Service` can serve a promoted model
- pipeline promotion can trigger or connect to serving
- KServe is understood as an optional later serving layer

Expected paths:

```text
src/kubeflow_by_doing/serve.py
src/kubeflow_by_doing/client.py
Dockerfile.serve
manifests/model-server/
components/deploy_model.py
components/smoke_test_model.py
```

Useful checks:

```bash
docker build -f Dockerfile.serve -t kubeflow-by-doing/serve:local .
kubectl -n kubeflow-by-doing rollout status deployment/model-server
uv run kbd-client predict --endpoint http://localhost:8000/predict --image-size 16
```

## 6. Local GPU

Expected outcome:

- `k3s` advertises GPU capacity if your machine has a supported NVIDIA GPU
- GPU training image builds
- GPU-aware KFP component requests `nvidia.com/gpu`
- CPU path remains usable
- GPU scheduling failures can be debugged with Kubernetes events

Expected paths:

```text
Dockerfile.gpu
infra/gpu/
src/kubeflow_by_doing/gpu.py
```

Useful checks:

```bash
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" allocatable gpu="}{.status.allocatable.nvidia\.com/gpu}{"\n"}{end}'
docker build -f Dockerfile.gpu -t kubeflow-by-doing/train:gpu-local .
```

## 7. STACKIT Expansion

Expected outcome:

- you can map the local architecture to STACKIT Kubernetes Engine
- cloud registry and object-storage boundaries are explicit
- KFP can run against SKE when credentials and budget are available
- cleanup is planned before cloud resources are created

Expected paths:

```text
infra/stackit/
scripts/stackit-*.py
scripts/stackit-*.sh
```

Useful checks:

```bash
kubectl config current-context
kubectl get nodes -o wide
```

## 8. Cloud Expansion

Expected outcome:

- provider-specific configuration is isolated in overlays
- pipeline code stays provider-neutral
- object storage and registry configuration can move across providers
- cleanup checklists are explicit

Expected paths:

```text
infra/cloud/
infra/cloud/overlays/
infra/cloud/secrets/
infra/cloud/checks/
infra/cloud/cleanup/
```

Useful checks:

```bash
uv run python infra/cloud/checks/object-storage-check.py
kubectl apply --dry-run=client -f infra/cloud/checks/image-pull-check.yaml
```

## 9. CI/CD

Expected outcome:

- local checks have CI equivalents
- image builds are separated from pipeline compilation
- pipeline submission is manual and guarded
- promotion can be represented as Git-tracked state
- secrets and expensive jobs are scoped

Expected paths:

```text
.github/workflows/
ci/
deploy/
```

Useful checks:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
uv run mkdocs build --strict
```

## 10. Capstone

Expected outcome:

- data ingestion and validation are explicit
- final pipeline ties training, evaluation, promotion, lineage, and optional serving together
- artifacts are durable outside pod filesystems
- capstone report can summarize the run
- cloud mapping is clear

Expected paths:

```text
components/ingest_data.py
components/validate_data.py
components/record_or_register_model.py
pipelines/capstone_pipeline.py
reports/capstone-runbook.md
compiled/capstone_pipeline.yaml
```

Useful checks:

```bash
uv run python pipelines/capstone_pipeline.py
kubectl -n kubeflow-by-doing get secret artifact-store-credentials
```

## 11. Conclusion

Expected outcome:

- you can explain what the tutorial built
- you can choose the next topic based on the bottleneck you actually have
- you know which topics are future study rather than core requirements

Useful checks:

```bash
uv run mkdocs build --strict
```

## 12. Flyte Add-On

Expected outcome:

- local Flyte workflow runs
- Flyte task boundaries are compared with KFP component boundaries
- optional k3s-backed Flyte run is documented
- Flyte remains outside the required Kubeflow path

Expected paths:

```text
flyte/
infra/flyte/
.flyte/
```

Useful checks:

```bash
uv run flyte --version
uv run python -m py_compile flyte/kbd_flyte_workflow.py
```

## 13. KServe Add-On

Expected outcome:

- KServe Standard mode is installed locally if the cluster version supports it
- a built-in sklearn `InferenceService` works
- KServe can read model artifacts from MinIO
- the tutorial model can be served through a custom predictor
- KServe tradeoffs are clear

Expected paths:

```text
infra/kserve/
src/kubeflow_by_doing/kserve_model.py
Dockerfile.kserve
```

Useful checks:

```bash
kubectl get pods -n kserve
kubectl -n kubeflow-by-doing get inferenceservice
docker build -f Dockerfile.kserve -t kubeflow-by-doing/kserve:local .
```

## 14. FAQ

Expected outcome:

- you can choose between namespace reset, KFP reset, and full `k3s` reset
- reset procedures link back to the setup chapters
- local state can be rebuilt intentionally

Useful checks:

```bash
kubectl config current-context
kubectl get namespaces
```

## When Something Is Missing

If a checkpoint mentions a file that does not exist yet, first confirm whether you have reached the chapter that creates it.

This repository is docs-first build-along content. Checked-in implementation files are reference state, but the tutorial expects readers to create files while following the chapters.
