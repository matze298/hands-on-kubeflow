# Project Structure

This page creates the project structure used by the local ML workflow.

The goal is to move from loose scripts to a small, testable Python package that can later be containerized and called from Kubeflow.

## What You Will Build

Create this structure from the repository root:

```text
kubeflow-by-doing/
├── src/
│   └── kubeflow_by_doing/
│       ├── __init__.py
│       ├── data.py
│       ├── model.py
│       ├── train.py
│       ├── evaluate.py
│       └── cli.py
├── components/
│   ├── __init__.py
│   ├── train_model.py
│   ├── evaluate_model.py
│   └── promote_model.py
├── pipelines/
│   ├── __init__.py
│   └── image_classification_pipeline.py
├── tests/
│   ├── test_data.py
│   ├── test_train.py
│   └── test_evaluate.py
├── compiled/
├── Dockerfile
└── pyproject.toml
```

## Why This Matters

Kubeflow should not be the first place where your training code is tested.

A healthier workflow is:

```text
plain Python function
  ↓
local CLI
  ↓
unit test
  ↓
container
  ↓
Kubernetes
  ↓
Kubeflow component
```

## Create the Folders

```bash
mkdir -p src/kubeflow_by_doing
mkdir -p components
mkdir -p pipelines
mkdir -p tests
mkdir -p compiled

touch src/kubeflow_by_doing/__init__.py
touch components/__init__.py
touch pipelines/__init__.py
```

## Folder Responsibilities

### `src/kubeflow_by_doing/`

The Python package. It contains the actual ML logic:

- data creation or loading
- training
- evaluation
- command-line entrypoints

This code should be testable without Kubeflow.

### `components/`

Thin KFP component wrappers.

A component answers:

```text
How does Kubeflow call the package code?
```

It should not contain the full ML implementation.

Later in the chapter, this folder grows from `train_model.py` and `evaluate_model.py` to also include `promote_model.py` for the evaluation gate.

### `pipelines/`

Pipeline composition.

A pipeline answers:

```text
Which components run, in which order, with which parameters?
```

It should not contain training loops.

### `tests/`

Local tests for core behavior.

### `compiled/`

Generated pipeline YAML files.

Depending on your repo policy, compiled pipelines can be committed for traceability or regenerated in CI.

## Target Dependency Direction

Prefer:

```text
tests/      → src/
components/          → src/
pipelines/           → components/
Dockerfile → src/
```

Avoid:

```text
src/ → components/
src/ → pipelines/
```

The core package should not know that Kubeflow exists.

## Common Problems

### Putting all logic into KFP components

This makes local testing harder.

Prefer:

```text
src/ contains logic
components/ call src/
```

### Putting pipeline code into `src/`

Pipeline code is orchestration code, not core package logic.

Keep it under `pipelines/`.

### Creating tutorial files in `/tmp`

For tutorial source, manifests, configs, and scripts, use tracked repository paths. Do not instruct readers to create durable tutorial files under `/tmp`.

## Acceptance Criteria

You are done when:

- the folder structure exists
- `src/kubeflow_by_doing/__init__.py` exists
- `components/__init__.py` exists
- `pipelines/__init__.py` exists
- you can explain the difference between `src/`, `components/`, and `pipelines/`

## Next Step

Continue with [Modern Python Tooling](02-modern-python-tooling.md).
