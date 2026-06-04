# Local ML Workflow

In this section, we turn a normal PyTorch project into a containerized workflow that can run inside Kubeflow.

The ML task is intentionally simple. The workflow is the lesson.

## What You Will Build

- production-shaped Python project
- modern Python tooling with uv, Ruff, ty, and pytest
- containerized training image
- PyTorch training component
- evaluation gate

## Why This Matters

Most ML code starts as a local script. Kubeflow becomes useful when that script can run reproducibly as a containerized component with explicit inputs, outputs, metrics, and artifacts.

## Acceptance Criteria

You are done with this section when:

- the training code runs locally
- the training code runs in a container
- the same logic runs as a KFP component
- the pipeline can decide whether to promote a model
