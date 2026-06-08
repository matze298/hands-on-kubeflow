# Local ML Workflow

In this chapter, we turn the toy Kubeflow Pipeline from Chapter 2 into a small but realistic local ML project.

The focus is not the model architecture. The reader already knows PyTorch and deep learning basics. The focus is the transition from local ML code to a testable, containerized, Kubeflow-orchestrated workflow.

From this chapter onward, the default local Kubernetes path is `MicroK8s` on WSL2. The `kind` cluster remains available as the starter and fallback path, but the ML workflow assumes the GPU-capable `MicroK8s` setup when possible.

```text
local ML script
  ↓
testable Python package
  ↓
containerized training entrypoint
  ↓
Kubeflow component
  ↓
pipeline with evaluation gate
```

## What You Will Build

During this chapter, you will create the target repository state:

```text
src/kubeflow_by_doing/
├── __init__.py
├── data.py
├── model.py
├── train.py
├── evaluate.py
└── cli.py

components/
├── __init__.py
├── train_model.py
├── evaluate_model.py
└── promote_model.py

pipelines/
├── __init__.py
└── image_classification_pipeline.py

tests/
├── test_data.py
├── test_train.py
└── test_evaluate.py

compiled/
Dockerfile
pyproject.toml
```

The repository may still be missing some or all of these files when you begin the chapter. In this tutorial, the Markdown pages are the primary build-along source of truth, and you create the implementation files as you go.

## Why This Matters

In Chapter 2, the pipeline components contained most logic directly inside decorated Python functions. That was useful for learning KFP, but it is not how we want to structure a real ML project.

A healthier structure is:

```text
core ML logic in src/
  ↓
thin CLI entrypoint
  ↓
container image
  ↓
thin KFP component wrapper
  ↓
pipeline composition
```

This gives us:

- local testability
- reproducible containers
- smaller pipeline files
- simpler debugging
- a clean path from local ML development to Kubernetes execution

## Chapter Flow

```text
project structure
  ↓
modern Python tooling
  ↓
local training script
  ↓
tests and quality checks
  ↓
containerized training
  ↓
training in Kubeflow
  ↓
evaluation gate
```

## Acceptance Criteria

You are done with Chapter 3 when:

- the project has a clean Python package under `src/`
- training can run locally through `uv run`
- evaluation can run locally through `uv run`
- tests pass with `uv run pytest`
- linting passes with `uv run ruff check`
- formatting passes with `uv run ruff format --check`
- type checking passes with `uv run ty check`
- a training image can be built locally
- the image can be loaded into the GPU-capable local cluster
- the training component can run inside Kubeflow
- the pipeline can make a simple metric-based promotion decision

## Next Step

Start with [Project Structure](01-project-structure.md).
