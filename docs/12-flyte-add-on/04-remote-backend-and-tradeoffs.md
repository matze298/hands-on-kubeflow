# Remote Backend and Tradeoffs

The local Flyte workflow is useful for comparison, but it is not the same thing as operating Flyte as a shared platform.

This page defines what changes when Flyte moves from local execution to a remote backend.

## Local vs Remote Flyte

Local Flyte execution is a developer loop:

```text
repository checkout
  ->
uv run flyte run --local
  ->
local run state
  ->
local TUI
```

Remote Flyte execution is a platform:

```text
repository checkout
  ->
package code and image context
  ->
remote Flyte backend
  ->
Kubernetes task pods
  ->
backend artifact storage
  ->
shared logs and run history
```

The remote shape is where Flyte becomes comparable to KFP as an orchestrator. It is also where platform responsibilities appear.

## What Must Exist Remotely

Before running this tutorial workflow on a remote Flyte backend, decide:

- which Kubernetes cluster hosts Flyte
- which object storage bucket backs task data
- which registry stores task images
- which identity mechanism users use
- which secret manager or Kubernetes Secret strategy is allowed
- which namespaces, queues, or projects separate workloads
- which nodes are CPU-only and which nodes can run GPU work
- who owns upgrades and incident response
- how idle resources are cleaned up

These are not Flyte-specific annoyances. They are the same platform boundaries you saw in the STACKIT and cloud expansion chapters.

## Cluster Mapping

For this repo, the mental model becomes:

```text
k3s
  local Kubeflow learning platform

STACKIT SKE or another managed Kubernetes provider
  cloud expansion platform

Remote Flyte backend
  optional alternate workflow orchestrator platform
```

Do not install Flyte into the core local path just because the dependency exists. The dependency lets readers run local Flyte commands. A backend deployment is a separate decision.

The next page makes that backend decision concrete for a local evaluation by installing Flyte into the tutorial's k3s cluster.

## Images

Remote tasks need images that the backend can run.

The first remote image should be CPU-only:

```text
registry.example.com/kubeflow-by-doing/flyte-cpu:<tag>
```

Add a GPU image only after CPU execution works:

```text
registry.example.com/kubeflow-by-doing/flyte-gpu:<tag>
```

Keep tags tied to:

- git SHA
- dependency lockfile state
- Python version
- CUDA version if GPU

Avoid `latest`. The CI/CD chapter already explained why mutable tags make debugging harder.

## Artifact Storage

A remote Flyte backend needs durable storage for task data.

You have two viable strategies:

1. Use Flyte backend-managed data storage for task handoff.
2. Preserve the tutorial's explicit object storage layout and pass URIs between tasks.

The first strategy is more Flyte-native. The second is easier to compare with the KFP and cloud chapters.

For this tutorial, prefer the explicit layout if your goal is platform comparison:

```text
s3://<bucket>/runs/<run_id>/
|-- models/
|-- metrics/
|-- reports/
|-- predictions/
`-- lineage/
```

That lets you compare KFP and Flyte while keeping the artifact contract stable.

## Secrets and Identity

A remote Flyte backend must answer:

```text
Who can submit workflows?
What credentials do tasks receive?
How are object storage credentials scoped?
How are registry credentials scoped?
How are secrets audited and rotated?
```

Do not solve this by adding environment files with real secrets to the repository.

Use the same rule as the cloud chapters:

```text
repository stores templates and names
platform stores secret values
tasks consume stable environment keys
```

Stable keys are useful even if the backend changes:

```text
KBD_ARTIFACT_BUCKET
KBD_S3_ENDPOINT_URL
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
```

## GPU Scheduling

Remote GPU Flyte tasks should be explicit.

The design should separate:

```text
CPU evaluation task
GPU training task
CPU promotion task
```

That prevents accidental GPU waste.

GPU readiness checks still apply:

- node pool exists
- device plugin or GPU operator works
- runtime can see CUDA
- image contains compatible PyTorch/CUDA libraries
- task requests match actual cluster resources
- queue or quota policy allows the job

If GPU scheduling fails, debug it like a Kubernetes workload:

```bash
kubectl get pods -A
kubectl describe pod <pod-name> -n <namespace>
kubectl get events -A --sort-by=.lastTimestamp
```

The orchestrator changes, but Kubernetes remains underneath.

## Observability

KFP and Flyte expose different run UIs, but operational questions stay similar:

- Which task failed?
- Which image did it run?
- Which parameters were used?
- Which artifact URI was written?
- Which logs explain the failure?
- Was the failure user code, platform infrastructure, or credentials?

For a remote Flyte backend, define a minimum run record:

```text
run_id
workflow version
git_sha
image tag
input parameters
model URI
metrics URI
promotion decision
failure reason if failed
```

Without that, switching orchestrators only moves confusion to a different UI.

## CI/CD Impact

The CI/CD chapter currently validates KFP artifacts:

```text
format, lint, type check, tests
build images
compile KFP pipeline YAML
optional submit
promotion state
```

A Flyte path changes the middle:

```text
format, lint, type check, tests
build Flyte task images
validate Flyte task module imports
optional run/deploy against Flyte backend
promotion state
```

Do not reuse the KFP compile step for Flyte. It validates the wrong artifact.

A minimal Flyte CI check could be:

```bash
export PYTHONPATH="$PWD/src"
uv run python -m py_compile flyte/kbd_flyte_workflow.py
uv run flyte --version
```

Only add remote submission after credentials, costs, and cleanup are clear.

## When to Stop at Local Flyte

Stop at local Flyte when:

- you only want to compare programming models
- no team has committed to operating Flyte
- there is no shared backend
- you do not need remote caching or shared run history
- the Kubeflow path already satisfies the course goal

That is a valid outcome. The add-on still served its purpose.

## When to Evaluate a Backend

Evaluate a remote backend when:

- several workflows would benefit from Flyte
- local runs are no longer enough
- shared run history matters
- remote resources and queues matter
- workflow code is easier to maintain in Flyte than KFP
- your platform team is willing to own Flyte operations

Do not evaluate a backend only because the local syntax looks pleasant.

## Final Tradeoff

Flyte is strongest here when:

```text
Python-first workflow authoring
typed task boundaries
local execution
narrower orchestrator surface
```

Kubeflow Pipelines is strongest here when:

```text
Kubeflow-native course path
KFP UI and SDK
compiled pipeline artifacts
alignment with KServe, Katib, Trainer, and Model Registry
```

Choose Flyte only when the benefits are worth adding a second orchestrator boundary.

## Acceptance Criteria

You are done when:

- you can describe the difference between local and remote Flyte
- you can list the infrastructure required for a remote backend
- you can explain how image and artifact strategy changes remotely
- you can explain why GPU tasks need explicit resource boundaries
- you can state how Flyte changes the CI/CD chapter
- you can decide whether local comparison is enough for your use case

## References

- [Flyte quickstart](https://www.union.ai/docs/v2/flyte/user-guide/quickstart/)
- [Flyte platform deployment](https://www.union.ai/docs/v2/flyte/deployment/)
- [Flyte key capabilities](https://www.union.ai/docs/v2/flyte/user-guide/core-concepts/key-capabilities/)
- [Flyte resources](https://www.union.ai/docs/v2/flyte/user-guide/configure-tasks/resources/)
- [Flyte secrets](https://www.union.ai/docs/v2/flyte/user-guide/configure-tasks/secrets/)

## Next Step

Continue with [Run Flyte on k3s](05-k3s-flyte-backend.md) when you want the Flyte comparison to run on Kubernetes instead of only in the local Python process.
