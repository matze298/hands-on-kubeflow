# Optional Flyte Add-On

This optional section compares the tutorial workflow with Flyte instead of Kubeflow Pipelines.

The core course remains a Kubeflow course. You already built the main path with:

```text
local Python code
  ->
containerized training
  ->
Kubeflow Pipelines
  ->
durable artifacts
  ->
evaluation and promotion
  ->
serving and cloud mapping
```

The Flyte add-on asks a narrower question:

```text
What changes if the workflow orchestrator is Flyte?
```

That question is worth answering because Flyte and KFP solve overlapping problems with different programming models. KFP is the natural fit for a Kubeflow-centered course. Flyte is often attractive when a team wants a Python-first workflow system with typed task boundaries, local execution, resource-aware tasks, and a smaller platform surface than full Kubeflow.

## What You Will Build

You will create an optional Flyte workflow file while following this add-on:

```text
flyte/
`-- kbd_flyte_workflow.py
```

The workflow will reuse the repository's existing training and evaluation functions:

```text
src/kubeflow_by_doing/train.py
src/kubeflow_by_doing/evaluate.py
```

The first version will use a small local teaching shortcut for the model handoff. Later pages explain durable Flyte files, object storage, backend tradeoffs, and a k3s-backed Flyte run.

## Add-On Structure

This add-on is split into six pages:

1. [Overview](00-overview.md)
2. [Flyte Concepts vs KFP](01-flyte-concepts-vs-kfp.md)
3. [Local Flyte Workflow](02-local-flyte-workflow.md)
4. [Artifacts, Resources, and Secrets](03-artifacts-resources-and-secrets.md)
5. [Remote Backend and Tradeoffs](04-remote-backend-and-tradeoffs.md)
6. [Run Flyte on k3s](05-k3s-flyte-backend.md)

The order matters. Start with the concept mapping, run the local workflow, study what must change for remote execution, then run the same workflow against a k3s-hosted Flyte backend.

## What Flyte Changes

Kubeflow Pipelines and Flyte can both express the same high-level ML workflow:

```text
train_model
  ->
evaluate_model
  ->
decide whether the result is acceptable
```

The difference is how you express and operate that workflow.

| Concern | Kubeflow Pipelines in this tutorial | Flyte add-on |
|---|---|---|
| Workflow shape | KFP pipeline function and component calls | Flyte tasks calling Flyte tasks |
| Task declaration | KFP component functions or component YAML | Python functions decorated with `@env.task` |
| Shared task config | Container image and component-level settings | `TaskEnvironment` |
| Local feedback | Compile pipeline YAML, then submit or inspect | Run a top-level task locally with Flyte CLI |
| Artifact handoff | KFP artifacts and mounted paths | Typed values plus file/directory types |
| UI habit | KFP UI | Flyte TUI locally, backend UI when remote |
| Kubeflow integration | Native course path | Separate orchestrator choice |

This does not make one system universally better. It makes the tradeoff explicit.

## Benefits of Flyte

Flyte is worth evaluating when these benefits matter:

- Python-first workflow authoring feels close to normal application code.
- Task signatures are typed, which makes data movement visible at function boundaries.
- Local execution is a useful feedback loop before remote execution.
- Task resources, secrets, caching, retries, and environment settings live near the task configuration.
- A team can use a workflow orchestrator without adopting the entire Kubeflow platform.
- The programming model is often approachable for Python-heavy ML teams.
- Remote Flyte runs still map to containerized execution on a backend, so the workflow is not trapped on one laptop.
- A k3s backend lets you evaluate Flyte with the same Kubernetes mental model used by the Kubeflow path.

For this tutorial, the strongest Flyte benefit is the local developer loop. You can express a workflow as normal Python tasks and run the top-level task from the repository root.

## Disadvantages of Flyte

Flyte also adds real costs:

- It is not Kubeflow Pipelines, so KFP SDK knowledge, compiled pipeline YAML, and KFP UI habits do not transfer directly.
- Existing KFP components need to be rewritten or wrapped.
- KServe, Katib, Kubeflow Trainer, and Kubeflow Model Registry remain separate integration choices.
- A remote Flyte backend is another platform to operate, secure, upgrade, and explain to users.
- Artifact handling still needs durable storage once tasks run in different containers.
- GPU scheduling, registry access, object storage, and secrets still need platform decisions.
- A local k3s backend is more realistic than local execution, but it is also more operational work.
- If the organization already standardized on Kubeflow, Flyte can become another workflow dialect to support.

Flyte can make workflow code cleaner. It does not remove platform engineering.

## How This Add-On Fits the Course

Treat the Flyte add-on as an evaluation track, not as required course material.

Use it when you want to answer:

- Would this workflow be easier to express in Flyte?
- Does local Flyte execution improve iteration speed?
- How much of the Kubeflow course knowledge still applies?
- Can the same Flyte workflow run as Kubernetes task pods on k3s?
- What platform operations would move from KFP to Flyte?
- Would a Flyte backend simplify or complicate our real environment?

Skip it when your goal is to finish the Kubeflow course path, run the capstone, or study Kubeflow-specific components.

## Prerequisites

Before starting this add-on, you should have completed:

- [Kubeflow Pipelines](../02-kubeflow-pipelines/00-overview.md), so KFP concepts are familiar
- [Local ML Workflow](../03-local-ml-workflow/00-overview.md), so the training and evaluation code exists
- [Artifacts and Tracking](../04-artifacts-and-tracking/00-overview.md), so artifact durability is familiar
- [Capstone](../10-capstone/00-overview.md) or [Conclusion and Future Reading](../11-conclusion/00-overview.md), so the full Kubeflow path is visible

For the local Flyte pages, no Kubernetes service needs to be running. For the k3s-backed Flyte page, restart the `k3s-kubeflow` profile from [Create a Local Kubernetes Cluster](../01-local-kubernetes/02-create-local-cluster.md) and make sure local object storage is available from [Install Local Object Storage](../04-artifacts-and-tracking/01-install-minio.md).

Flyte is already included in this repository's dependencies:

```bash
uv run flyte --version
```

Expected shape:

```text
Flyte SDK version: 2.x.x
```

## Acceptance Criteria

You are done with the overview when:

- you understand that Flyte is optional in this tutorial
- you can state why Flyte is being compared with KFP
- you can name the six add-on pages and the order to read them
- you can explain one benefit and one cost of introducing Flyte

## References

- [Flyte quickstart](https://www.union.ai/docs/v2/flyte/user-guide/quickstart/)
- [Flyte tasks](https://www.union.ai/docs/v2/flyte/user-guide/core-concepts/tasks/)
- [Flyte key capabilities](https://www.union.ai/docs/v2/flyte/user-guide/core-concepts/key-capabilities/)

## Next Step

Continue with [Flyte Concepts vs KFP](01-flyte-concepts-vs-kfp.md).
