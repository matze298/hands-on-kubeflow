# Verification Matrix

Use this page as a checklist for proving each part of the tutorial still works.

The tutorial is build-along content. Some checks only become available after you create the files in the matching chapter. Run the checks from the repository root unless a chapter says otherwise.

## Check Types

| Type | Meaning |
|---|---|
| Local | runs on the development machine without Kubernetes |
| Kubernetes | requires the current `kubectl` context to point at the tutorial cluster |
| MicroK8s | assumes the default local ML platform from Chapter 1 |
| GPU | requires a working NVIDIA GPU path |
| Cloud | may require provider credentials or billable resources |
| Optional | outside the required Kubeflow path |

## Core Path

| Chapter | Scope | Type | Primary checks |
|---|---|---|---|
| 0. Orientation | course map and expectations | Local | `uv run mkdocs build --strict` |
| 1. Local Kubernetes | toolchain, `kind`, `MicroK8s`, GPU smoke tests | Local, Kubernetes, MicroK8s, GPU | `kubectl get nodes`, `kubectl get pods -A`, `docker run --rm --gpus all ...`, GPU smoke-test pod logs |
| 2. Kubeflow Pipelines | standalone KFP install and starter pipelines | Local, Kubernetes | `kubectl get pods -n kubeflow`, `uv run python pipelines/hello_pipeline.py`, `uv run python pipelines/tiny_ml_pipeline.py`, KFP UI port-forward |
| 3. Local ML Workflow | package code, tests, container, KFP training pipeline | Local, Kubernetes | `uv run pytest`, `uv run ruff check .`, `uv run ty check`, `docker build -t kubeflow-by-doing/train:local .`, `uv run python pipelines/image_classification_pipeline.py` |
| 4. Artifacts and Tracking | MinIO, artifact layout, MLflow, lineage | Local, Kubernetes | `kubectl -n minio get pods`, MinIO bucket smoke test, `kubectl -n kubeflow-by-doing get secret artifact-store-credentials`, MLflow port-forward, object-storage artifact listing |
| 5. Local Serving | FastAPI server, serving image, Kubernetes deployment | Local, Kubernetes | local API smoke test, `docker build -f Dockerfile.serve -t kubeflow-by-doing/serve:local .`, `kubectl -n kubeflow-by-doing rollout status deployment/model-server`, prediction smoke test |
| 6. Local GPU | GPU image, GPU-aware KFP components, scheduling debugging | MicroK8s, GPU | GPU allocatable JSONPath check, PyTorch GPU pod logs, GPU image smoke test, KFP GPU run pod events |
| 10. Capstone | full local end-to-end workflow | Local, Kubernetes, MicroK8s | capstone pipeline compile, required services ready, final run artifacts exist, smoke test passes if serving is enabled, capstone report generated |

## Expansion Tracks

| Chapter | Scope | Type | Primary checks |
|---|---|---|---|
| 7. STACKIT Expansion | STACKIT Kubernetes Engine, registry, object storage, GPU node pool | Cloud | kubeconfig context check, registry push/pull smoke test, object-storage smoke test, KFP run on SKE, explicit cleanup checklist |
| 8. Cloud Expansion | provider-neutral overlays and portability checks | Cloud | provider env file review, generated secret manifests, image-pull check pod, object-storage check script, cleanup plan review |
| 9. CI/CD | local quality gate mapped to GitHub Actions | Local, Cloud | `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check`, `uv run pytest`, `uv run mkdocs build --strict`, pipeline compile workflow, guarded submit workflow |

## Optional Add-Ons

| Chapter | Scope | Type | Primary checks |
|---|---|---|---|
| 11. Conclusion | next-topic decision points and alternatives | Local | link/navigation review, `uv run mkdocs build --strict` |
| 12. Flyte Add-On | local Flyte workflow and MicroK8s-backed Flyte run | Optional, Local, MicroK8s | `uv run flyte --version`, local Flyte run, Helm render for Flyte backend values, Flyte config check, MicroK8s task pod inspection |
| 13. FAQ | reset procedures | Local, Kubernetes, MicroK8s | commands are reviewed against the current setup chapters, `uv run mkdocs build --strict` |
| 14. KServe Add-On | KServe Standard mode and optional `InferenceService` serving | Optional, Kubernetes, MicroK8s | `kubectl get pods -n kserve`, `kubectl get inferenceservice -n kubeflow-by-doing`, first sklearn prediction, tutorial model prediction |

## Repo-Level Checks

Run these before publishing broad tutorial edits:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
uv run mkdocs build --strict
git diff --check
```

Run these when pipeline files or component files change:

```bash
uv run python pipelines/hello_pipeline.py
uv run python pipelines/tiny_ml_pipeline.py
uv run python pipelines/tiny_ml_pipeline_refactored.py
uv run python pipelines/image_classification_pipeline.py
```

Do not include `pipelines/submit_hello_pipeline.py` in the default local compile check. It talks to a running KFP endpoint and belongs in a Kubernetes-backed or CI submit check.

## What To Do When a Check Fails

Use the narrowest failing layer:

| Failing check | Start debugging with |
|---|---|
| local Python tests | the relevant `src/` module and test file |
| pipeline compilation | KFP imports, component annotations, and generated YAML |
| image build | Dockerfile, dependency lockfile, and build context |
| image pull in Kubernetes | registry tag, image import/push, and pull secret |
| pod pending | `kubectl describe pod` and namespace events |
| pod crash | container logs, command arguments, mounted paths, and secrets |
| artifact upload | MinIO/service endpoint, bucket existence, and credentials |
| GPU scheduling | node allocatable GPU, device plugin, resource requests, taints, and image CUDA compatibility |
| cloud run | provider context, registry, object storage, credentials, quota, and cleanup state |
