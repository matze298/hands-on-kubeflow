# Artifacts, Resources, and Secrets

The local Flyte workflow used a deliberate shortcut: it encoded a tiny model artifact into a string.

That helped you focus on task shape. It is not the production shape.

This page explains what must change when a Flyte workflow starts to look like real MLOps:

- model artifacts should be durable
- task resources should be explicit
- secrets should not be embedded in code
- GPU and CPU tasks should be separated deliberately

## Why the Local Shortcut Is Not Enough

The local workflow used this pattern:

```python
model_bytes = (output_dir / "model.pt").read_bytes()
return base64.b64encode(model_bytes).decode("ascii")
```

That pattern is intentionally limited:

- it only works for small artifacts
- it hides the artifact as an inline value
- it is inefficient for real model files
- it does not create the same artifact layout used by the rest of the tutorial
- it teaches the wrong habit if copied into remote workflows

The durable version should preserve the tutorial lesson:

```text
task-local filesystem = temporary
artifact storage      = durable
```

## Durable Artifact Options

There are three practical patterns.

| Pattern | Use when | Avoid when |
|---|---|---|
| Typed file/directory objects | you want Flyte to manage artifact handoff | you need an externally defined object storage layout |
| Explicit object storage paths | you already have a stable `s3://<bucket>/runs/<run_id>/...` contract | you want Flyte to abstract storage details |
| Inline values | values are small, structured, and truly parameters or metrics | values are large files, models, datasets, or reports |

For this tutorial, the KFP path established an explicit artifact layout:

```text
s3://<bucket>/runs/<run_id>/
|-- models/
|-- metrics/
|-- reports/
|-- predictions/
`-- lineage/
```

If you were adopting Flyte seriously, decide whether to keep that layout or let Flyte's backend-managed data layer become the primary artifact contract.

## Flyte File and Directory Types

In Flyte SDK 2.4.4, file and directory types are available from `flyte.io`:

```python
from flyte.io import Dir, File
```

A production-shaped model task should return a durable file or directory abstraction, not a base64 string.

Conceptually, the target shape is:

```python
from pathlib import Path

import flyte
from flyte.io import Dir

from kubeflow_by_doing.train import train


env = flyte.TaskEnvironment(name="kubeflow-by-doing-flyte")


@env.task
def train_model_task(
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
) -> Dir:
    output_dir = Path("outputs/flyte/model")
    output_dir.mkdir(parents=True, exist_ok=True)
    train(
        output_dir=output_dir,
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
        device="cpu",
    )
    return Dir(path=str(output_dir))
```

Do not return a `Dir` that points into a `TemporaryDirectory` after the context exits. Python deletes that directory before the orchestrator can safely materialize the returned artifact.

The exact remote behavior depends on the Flyte backend storage configuration. That backend decision is part of platform setup, not task business logic.

## Explicit Object Storage Paths

If you want the Flyte workflow to preserve the tutorial's artifact layout, pass an explicit artifact root:

```python
import os
from pathlib import Path

import boto3
from botocore.client import Config


def upload_file(local_path: Path, remote_uri: str) -> None:
    if not remote_uri.startswith("s3://"):
        raise ValueError("model_uri must start with s3://")

    bucket_and_key = remote_uri.removeprefix("s3://")
    bucket, key = bucket_and_key.split("/", 1)

    client = boto3.client(
        "s3",
        endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        config=Config(signature_version="s3v4"),
    )
    client.upload_file(str(local_path), bucket, key)


@env.task
def train_model_task(
    run_id: str,
    artifact_root: str,
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
) -> str:
    model_uri = f"{artifact_root}/runs/{run_id}/models/model.pt"
    output_dir = Path("outputs/flyte/model")
    train(
        output_dir=output_dir,
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
        device="cpu",
    )
    upload_file(output_dir / "model.pt", model_uri)
    return model_uri
```

This helper follows the same S3-compatible storage pattern used in Chapter 4. It expects the object-storage dependency and environment variables from that chapter to be present when you run this exact task.

That shape keeps storage ownership clear:

```text
pipeline parameter -> artifact_root
task writes        -> model_uri
next task reads    -> model_uri
```

This is closer to the provider-neutral cloud chapters because the workflow can receive:

```text
artifact bucket
S3-compatible endpoint
region
credentials
run_id
```

The cost is that your task code now owns more storage logic.

## Resource Requests

Flyte resources can be attached to a `TaskEnvironment`:

```python
import flyte


cpu_env = flyte.TaskEnvironment(
    name="kbd-cpu",
    resources=flyte.Resources(cpu="1", memory="2Gi"),
)
```

Use separate environments when resource needs differ:

```python
gpu_env = flyte.TaskEnvironment(
    name="kbd-gpu",
    resources=flyte.Resources(cpu="2", memory="8Gi", gpu="T4:1"),
)
```

Do not copy a GPU request into every task. Evaluation, metadata checks, and small validation work usually do not need GPU.

For this tutorial:

```text
CPU env -> evaluation, promotion decisions, smoke checks
GPU env -> training task only
```

That matches the principle from the Local GPU chapter: request accelerators only where they are actually needed.

## Images and Dependencies

The local example uses the repository environment. A remote Flyte backend needs an image strategy.

Think in two layers:

```text
image layer:
  Python interpreter
  installed dependencies
  system libraries
  torch
  flyte

code layer:
  flyte/kbd_flyte_workflow.py
  src/kubeflow_by_doing/
```

Flyte has project patterns for `uv`-based repositories. The important lesson is the same as the Docker chapters: do not let every code edit force an expensive image rebuild if the dependency layer did not change.

For a first remote experiment, keep the image boring:

- same Python version policy as the repo
- same `uv.lock`
- same PyTorch dependency
- same training package
- explicit CPU image first
- GPU image only after CPU works

## Secrets

Do not put credentials in Flyte task code.

The tutorial's provider-neutral secret keys include:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
KBD_S3_ENDPOINT_URL
KBD_ARTIFACT_BUCKET
MLFLOW_TRACKING_URI
MLFLOW_EXPERIMENT_NAME
```

In a remote Flyte setup, secrets should be provided by the platform. Flyte's SDK exposes a `Secret` configuration object:

```python
import flyte


storage_secret = flyte.Secret(
    key="AWS_ACCESS_KEY_ID",
    group="artifact-store",
    as_env_var="AWS_ACCESS_KEY_ID",
)
```

For this tutorial, treat the exact backend secret wiring as platform setup. The task should know the environment variable names it needs, not the secret manager internals.

## Caching and Retries

Flyte supports caching and retry-related configuration, but do not add them reflexively.

Good candidates for caching:

- deterministic data preparation
- feature generation with fixed inputs
- expensive validation steps with stable inputs

Poor candidates for caching:

- training that intentionally depends on fresh data
- tasks that read mutable external state without versioned inputs
- tasks where the cost of stale results is higher than recomputation

For retries, ask whether the failure is transient:

```text
registry timeout       -> retry may help
object store timeout   -> retry may help
bad model code         -> retry will waste time
invalid credentials    -> retry will not help
```

This is the same engineering judgment you used in Kubernetes debugging chapters.

## Promotion Outputs

The local Flyte workflow returns:

```python
return {
    "accuracy": accuracy,
    "promoted": 1.0 if accuracy >= min_accuracy else 0.0,
}
```

That is enough for a local comparison. A production workflow should write a durable promotion record:

```text
runs/<run_id>/lineage/promotion.json
```

The record should include:

- run ID
- model URI
- metrics URI
- threshold
- decision
- git SHA
- image tag
- timestamp

This keeps the Flyte path aligned with the tutorial's lineage lesson.

## Acceptance Criteria

You are done when:

- you can explain why base64 model handoff is a teaching shortcut
- you can name when to use typed files/directories
- you can name when to keep explicit object storage paths
- you can define separate CPU and GPU task environments
- you can explain why secrets belong in platform configuration
- you can identify which tasks are safe caching candidates

## References

- [Flyte files and directories](https://www.union.ai/docs/v2/flyte/user-guide/build-tasks/files-and-directories/)
- [Flyte resources](https://www.union.ai/docs/v2/flyte/user-guide/configure-tasks/resources/)
- [Flyte secrets](https://www.union.ai/docs/v2/flyte/user-guide/configure-tasks/secrets/)
- [Flyte monorepo with uv pattern](https://www.union.ai/docs/v2/flyte/user-guide/project-patterns/monorepo-with-uv/)

## Next Step

Continue with [Remote Backend and Tradeoffs](04-remote-backend-and-tradeoffs.md).
