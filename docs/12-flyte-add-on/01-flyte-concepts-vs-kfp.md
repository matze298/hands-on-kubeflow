# Flyte Concepts vs KFP

This page maps the concepts you learned in Kubeflow Pipelines to Flyte.

The goal is not to memorize a second vocabulary. The goal is to understand which parts of the workflow are the same and which parts move to different abstractions.

## The Same Workflow Shape

The tutorial workflow is intentionally small:

```text
train
  ->
evaluate
  ->
decide whether the metric is acceptable
```

That shape survives the orchestrator change.

What changes is how the orchestrator sees each boundary:

| Workflow concern | KFP version | Flyte version |
|---|---|---|
| Unit of work | Component task | Task |
| Workflow container | Pipeline function | Top-level task |
| Task configuration | Component image, resources, inputs, outputs | `TaskEnvironment` plus task signature |
| Data contract | KFP parameters and artifacts | Python type hints |
| Local run mode | Compile locally, submit to KFP backend | Run locally through Flyte CLI |
| Remote run mode | KFP backend creates workflow pods | Flyte backend creates task pods |
| Artifact model | Pipeline artifacts and mounted paths | Typed values plus file/directory objects |

You should recognize the platform lesson: tasks are isolated units, and anything crossing a task boundary needs an explicit contract.

## KFP Pipeline Function vs Flyte Top-Level Task

In KFP, the pipeline function describes the graph:

```python
@pipeline(name="image-classification-local")
def image_classification_pipeline(
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
) -> None:
    train_task = train_model(
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
    )
    evaluate_model(
        model=train_task.outputs["model"],
        seed=seed,
    )
```

The pipeline function is not normal training code. It defines a workflow graph that the KFP compiler turns into pipeline YAML.

In Flyte 2, the top-level task can call other tasks:

```python
@env.task
def flyte_image_classification_pipeline(
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
) -> dict[str, float]:
    model = train_model_task(
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
    )
    accuracy = evaluate_model_task(
        encoded_model=model,
        seed=seed,
    )
    return {"accuracy": accuracy}
```

This can feel more direct because the workflow looks like normal Python. The tradeoff is that the function call still has workflow semantics. When the workflow runs remotely, called tasks may execute in separate containers.

## Component Inputs vs Type Hints

KFP components in this repo use explicit inputs and outputs:

```text
epochs
learning_rate
seed
n_train
n_val
batch_size
model artifact
metrics artifact
```

Flyte leans on Python type hints:

```python
@env.task
def evaluate_model_task(
    encoded_model: str,
    seed: int = 42,
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> float:
    return 0.91
```

That is a real advantage for Python-heavy teams. The task contract is visible in the function signature.

It also means you should be disciplined:

- keep task inputs small and explicit
- do not hide configuration in global variables
- do not pass large model payloads as strings in production
- prefer typed files/directories or object storage paths for large artifacts

## Component Image vs TaskEnvironment

In KFP, image choice often appears at the component boundary. The tutorial spends time making training images explicit because Kubernetes pulls and runs those images.

In Flyte, common task configuration lives in a `TaskEnvironment`:

```python
import flyte

env = flyte.TaskEnvironment(
    name="kubeflow-by-doing-flyte",
    resources=flyte.Resources(cpu="1", memory="2Gi"),
)
```

Tasks that use `@env.task` share that environment unless you create separate environments.

For this tutorial, one environment is enough for the first CPU workflow. If you later add a GPU workflow, split environments deliberately:

```text
cpu_env -> data prep, evaluation, small checks
gpu_env -> GPU training
```

That mirrors the tutorial's KFP distinction between CPU and GPU components.

## Pipeline YAML vs Code Execution

KFP has an explicit compile step:

```bash
uv run python pipelines/image_classification_pipeline.py
```

That produces:

```text
compiled/image_classification_pipeline.yaml
```

This is useful in CI/CD because pipeline compilation becomes a build artifact and validation step.

Flyte's local loop is different:

```bash
uv run flyte run --local flyte/kbd_flyte_workflow.py flyte_image_classification_pipeline
```

That is shorter when experimenting locally. It is less directly aligned with the KFP CI/CD chapters because the artifact is no longer a compiled KFP pipeline YAML.

The practical question is:

```text
Do you want a KFP artifact-centered workflow, or a Flyte task-centered workflow?
```

Neither answer is automatically right.

## Artifact Thinking Is Still Required

The biggest mistake when comparing orchestrators is to focus only on syntax.

This is not enough:

```text
KFP DSL vs Flyte Python syntax
```

The real platform question is:

```text
Where does every artifact live when each task runs in an isolated container?
```

KFP made this visible with artifact paths. Flyte makes it visible through typed values, file/directory types, and backend storage.

For small local examples, you can use a teaching shortcut. For real remote execution, model files, metrics, reports, and lineage records must be durable outside task-local temporary directories.

## Benefits in This Tutorial Context

Flyte gives this tutorial a useful contrast:

- It shows that the workflow is not inherently tied to KFP.
- It makes task typing feel more direct.
- It gives a concise local execution loop.
- It demonstrates a narrower workflow-orchestrator choice.
- It reinforces the same container and artifact lessons from Kubeflow.

The add-on also helps you evaluate your own platform bias. If you prefer Flyte after this comparison, you should be able to say exactly why.

## Costs in This Tutorial Context

Flyte also introduces divergence:

- The docs must explain a second workflow vocabulary.
- CI/CD chapters built around KFP compilation no longer map one-to-one.
- KFP UI screenshots and run debugging habits no longer apply.
- Kubeflow component integration becomes less direct.
- Remote Flyte deployment would need its own platform chapter if this became a full course.

That is why this section is after the conclusion. It is useful, but it should not interrupt the core Kubeflow path.

## Decision Rule

Use this rule when evaluating Flyte:

| If you care most about... | Prefer... |
|---|---|
| learning Kubeflow end to end | KFP |
| staying close to KServe, Katib, Trainer, and Kubeflow Model Registry | KFP |
| Python-first task authoring | Flyte |
| short local workflow iteration | Flyte |
| one orchestrator for a Kubeflow platform | KFP |
| workflow orchestration without full Kubeflow | Flyte |

The rest of this add-on makes that comparison concrete.

## Acceptance Criteria

You are done when:

- you can map KFP components to Flyte tasks
- you can map a KFP pipeline function to a Flyte top-level task
- you can explain why type hints matter in Flyte
- you can explain why artifact durability still matters
- you can name one case where KFP is the better choice
- you can name one case where Flyte is the better choice

## References

- [Flyte tasks](https://www.union.ai/docs/v2/flyte/user-guide/core-concepts/tasks/)
- [Flyte key capabilities](https://www.union.ai/docs/v2/flyte/user-guide/core-concepts/key-capabilities/)
- [Kubeflow Pipelines components](https://www.kubeflow.org/docs/components/pipelines/concepts/component/)

## Next Step

Continue with [Local Flyte Workflow](02-local-flyte-workflow.md).
