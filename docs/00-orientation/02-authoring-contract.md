# Authoring Contract

This page defines how chapters in this tutorial should be generated, refined, and validated.

## Workflow

The intended authoring workflow is:

```text
Generate chapter prose with ChatGPT
  ↓
refine structure, wording, and integration with Claude or Codex
  ↓
validate commands locally
  ↓
commit Markdown, code, manifests, and tests together
  ↓
serve with MkDocs
```

ChatGPT is used to create the first complete prose draft.

Claude or Codex can then improve clarity, fix inconsistencies, tighten wording, validate code structure, and integrate the chapter with the repository.

## Output Format

Every chapter must be written as MkDocs-compatible Markdown.

Chapter files should live under `docs/`.

Code, manifests, and scripts should not be hidden inside prose-only chapters when they are meant to be used directly. They should live in appropriate repository folders, for example:

```text
src/
components/
pipelines/
manifests/
infra/
examples/
tests/
```

The Markdown chapter should explain the files and show the relevant excerpts, but the runnable source of truth should be in the repo.

## Chapter Template

Each chapter should follow this structure unless there is a strong reason not to:

```markdown
# Chapter Title

## What You Will Build

## Why This Matters

## Prerequisites

## Concepts

## Hands-On

## Verify the Result

## Common Problems

## Cleanup

## What You Learned

## References

## Acceptance Criteria

## Next Step
```

For short conceptual orientation chapters, the template may be simplified.

For hands-on chapters, verification and acceptance criteria are mandatory.

## Granularity Rules

Be concise when covering topics the reader already knows:

- Python basics
- PyTorch basics
- deep learning fundamentals
- basic Git usage
- basic command-line usage

Use medium depth when covering topics that are central and likely new:

- Kubernetes workloads
- Kubeflow Pipelines
- artifact passing
- object storage in Kubernetes
- GPU scheduling
- local image handling
- pipeline debugging
- model promotion
- serving in Kubernetes

Avoid deep theory unless the chapter requires it.

## Motivation Rule

When introducing a concept, briefly motivate it from the perspective of an ML engineer.

Good:

```text
A Kubernetes Job is the simplest mental model for a training run: start a container, run to completion, keep logs and status.
```

Less useful:

```text
A Job creates one or more Pods and ensures that a specified number successfully terminate.
```

The second sentence may still appear, but after the ML motivation.

## Reference Rule

If a concept is important but not central to the chapter, summarize it briefly and link to further reading.

Examples:

- PyTorch training loops
- Docker image layering
- Kubernetes CNI details
- advanced object storage policies
- Helm chart authoring
- service mesh internals

## Tooling Rule

Prefer current tooling:

- `uv`
- `ruff`
- `ty`
- `pytest`
- `marimo`
- `mkdocs-material`
- `prek` for Git hooks
- `kind` or `k3d`
- KFP v2-style pipelines
- modern Kubernetes manifests
- reproducible container builds

Do not default to legacy choices unless the ecosystem forces it.
If a chapter introduces repository commands, prefer the `uv run ...` form and keep the hook story aligned with `prek.toml` and `setup.py`.

## Local-First Rule

The core tutorial must run locally.

Cloud chapters are expansion chapters.

The main learning path is:

```text
local Linux / WSL2 machine
  ↓
local Kubernetes
  ↓
local Kubeflow Pipelines
  ↓
local artifacts and tracking
  ↓
local model serving
```

STACKIT, managed Kubernetes, cloud object storage, and CI/CD come later.

## GPU Rule

The core environment assumes Linux or WSL2 with an NVIDIA GPU.

GPU support should be treated as part of the local ML-ready platform, not only as a cloud topic.

Where practical, commands should provide CPU fallback for readers validating the logic without a GPU.

## Notebook Rule

Do not use Jupyter notebooks in the core path.

Prefer scripts and pipelines.

If interactive exploration is helpful, use marimo.

## Acceptance Criteria Rule

Every hands-on chapter must end with acceptance criteria.

Example:

```markdown
## Acceptance Criteria

You are done when:

- `kubectl get nodes` shows a ready local cluster.
- a test Kubernetes Job completes successfully.
- logs can be inspected with `kubectl logs`.
- cleanup commands return the machine to a known state.
```

## Style Rule

Write like a practical engineering tutorial:

- short paragraphs
- commands the reader can run
- expected outputs where useful
- no unexplained walls of YAML
- no unexplained magic scripts
- debugging guidance close to the commands
- references for deeper reading

The goal is not to maximize completeness.

The goal is to keep the reader moving while making every new concept understandable.
