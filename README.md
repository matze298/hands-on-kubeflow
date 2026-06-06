# Kubeflow by Doing

This repository is tailored to a local-first, GPU-aware Kubeflow tutorial for readers who want to build practical Kubernetes-native MLOps workflows with Python, PyTorch, and Kubeflow Pipelines.

The tutorial starts with `kind` for the first Kubernetes basics and then uses `MicroK8s` on WSL2 as the default local ML platform. `kind` stays available as the starter and fallback path.

The repository is meant to work both as the published tutorial source and as a reference implementation. Readers should be able to start from a clean checkout and create the files themselves while following the chapters, while the checked-in files represent the target state those steps are working toward.

## Run Locally

```bash
./setup.py
mkdocs serve
```
