# Version Compatibility

Use this page before upgrading dependencies, Kubernetes components, container base images, or Helm charts.

The tutorial is intentionally local-first, but it still depends on several moving parts. Upgrade one layer at a time, rerun the matching checks, and review generated pipeline YAML when KFP-related code changes.

## Repository Tooling

| Tool | Current policy | Where to check |
|---|---|---|
| Python | `>=3.14` | `pyproject.toml` |
| dependency manager | `uv` | `setup.py`, `pyproject.toml`, `uv.lock` |
| lint and format | `ruff` | `pyproject.toml`, `ruff.toml`, `uv.lock` |
| type checking | `ty` | `pyproject.toml`, `ty.toml`, `uv.lock` |
| tests | `pytest` | `pyproject.toml`, `tests/` |
| docs | `mkdocs-material` | `pyproject.toml`, `mkdocs.yml` |
| Git hooks | `prek` | `prek.toml`, `pyproject.toml` |

Baseline local check:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
uv run mkdocs build --strict
```

## Python Packages

| Package | Tutorial role | Compatibility notes |
|---|---|---|
| `kfp` | pipeline DSL, compiler, and client | Keep component annotations runtime-resolvable. Do not hide KFP artifact types behind `TYPE_CHECKING` in component or pipeline files. |
| `torch` | training, evaluation, and serving model runtime | Keep CPU/GPU image tags aligned with the locked PyTorch version and the host NVIDIA driver. |
| `typer` and `rich` | local tutorial CLI | Recheck CLI commands after changing Typer. |
| `boto3` | S3-compatible object storage client | Required once Chapter 4 object storage is added. |
| `mlflow` | local experiment tracking | Keep the client package compatible with the MLflow server image used in the Kubernetes manifest. |
| `fastapi`, `uvicorn`, `pydantic` | model serving | Recheck request/response validation and local server startup after upgrades. |
| `flyte[tui]` | optional Flyte add-on | Keep Flyte SDK examples aligned with the installed SDK and the backend chart used in Chapter 12. |

## Kubernetes and Cluster Components

| Component | Tutorial role | Upgrade check |
|---|---|---|
| `kind` | starter and CPU fallback cluster | Recreate starter cluster and rerun Chapter 1 jobs. |
| `MicroK8s` | default local ML/Kubeflow cluster | Check DNS, storage, registry, GPU addon, and node readiness. |
| NVIDIA driver and container runtime | GPU support | Rerun host `nvidia-smi`, Docker GPU smoke test, and Kubernetes GPU smoke test. |
| standalone KFP manifests | local Kubeflow Pipelines backend | Reinstall in `kubeflow`, then compile and submit the starter pipeline. |
| MinIO image | local S3-compatible object storage | Recreate bucket and rerun object-storage smoke tests. |
| MLflow image | tracking server | Check tracking UI, experiment creation, and artifact logging. |
| Flyte Helm chart | optional MicroK8s-backed Flyte run | Render values, deploy, check projects, then inspect task pods. |
| KServe | optional `InferenceService` serving layer | Check Kubernetes version, CRDs, controller pods, serving runtimes, and predictor pods. |

## Container Images

| Image | Compatibility rule |
|---|---|
| `python:3.12-slim` snippets | Used in lightweight component examples and init containers. Keep snippets simple and dependency installs explicit. |
| `pytorch/pytorch:*cuda*` | Match CUDA support to the host driver and the locked PyTorch version. |
| `ghcr.io/mlflow/mlflow:*` | Match server behavior to the local `mlflow` client package where practical. |
| `quay.io/minio/minio:*` | Keep S3 API behavior compatible with `boto3` smoke tests. |
| `nvidia/cuda:*base*` | Use a CUDA version supported by the host driver and MicroK8s GPU setup. |
| KServe predictor image | Keep the custom predictor image aligned with the tutorial package, `kserve` SDK, and the model checkpoint format. |

When changing image tags, rerun the narrow smoke test first, then rerun the affected chapter checks.

## KFP Annotation Rules

KFP inspects component and pipeline annotations while decorators and compilation run. For files that define KFP components or pipelines:

- import KFP DSL artifact types at runtime
- avoid `from __future__ import annotations`
- avoid hiding KFP artifact imports behind `TYPE_CHECKING`
- recompile the pipeline after changing component signatures
- review `compiled/*.yaml` diffs before committing them

Pipeline compile check:

```bash
uv run python pipelines/hello_pipeline.py
uv run python pipelines/tiny_ml_pipeline.py
uv run python pipelines/tiny_ml_pipeline_refactored.py
uv run python pipelines/image_classification_pipeline.py
```

## Upgrade Checklist

Use this order for broad dependency upgrades:

1. Update one layer: Python packages, Kubernetes manifests, base images, or Helm chart values.
2. Regenerate the lockfile when Python dependencies change.
3. Run the repo-level local checks.
4. Recompile pipeline YAML when KFP components or pipeline files are touched.
5. Run the smallest Kubernetes smoke test for the changed layer.
6. Review generated YAML and docs snippets together.
7. Update this page if a new compatibility rule appears.

Use the [Verification Matrix](verification-matrix.md) to choose the chapter-level checks after an upgrade.
