# Debugging KFP Runs

A Kubeflow pipeline step is still a Kubernetes workload.

This page connects the KFP UI to the Kubernetes debugging loop from Chapter 1.

If you are following along in the repository, this page is the target implementation for `pipelines/failing_pipeline.py`.

## What You Will Build

You will intentionally create a failing pipeline and debug it through:

- the KFP UI
- step logs
- Kubernetes pods
- Kubernetes events

## Why This Matters

KFP gives you a workflow view.

Kubernetes gives you the runtime truth.

When a pipeline fails, you need both views:

```text
KFP UI: which step failed?
Kubernetes: why did the container fail?
```

## Create a Failing Pipeline

Create `pipelines/failing_pipeline.py`:

```python
from kfp import compiler, dsl


@dsl.component(base_image="python:3.12-slim")
def start_step() -> str:
    print("start step succeeded")
    return "data-uri-placeholder"


@dsl.component(base_image="python:3.12-slim")
def failing_step(data_uri: str) -> None:
    print(f"received {data_uri=}")
    raise RuntimeError("simulated KFP component failure")


@dsl.component(base_image="python:3.12-slim")
def never_runs() -> None:
    print("this should not run")


@dsl.pipeline(name="failing-pipeline")
def failing_pipeline() -> None:
    start_task = start_step()
    failed_task = failing_step(data_uri=start_task.output)
    never_runs().after(failed_task)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=failing_pipeline,
        package_path="compiled/failing_pipeline.yaml",
    )
```

Compile it:

```bash
uv run python pipelines/failing_pipeline.py
```

Upload and run `compiled/failing_pipeline.yaml` in the KFP UI.

## Inspect the Failure in the UI

In the KFP UI:

1. open the failed run
2. find the failed step
3. open logs
4. confirm the error message

Expected message:

```text
RuntimeError: simulated KFP component failure
```

## Find the Kubernetes Pod

List recent pods across namespaces:

```bash
kubectl get pods -A --sort-by=.metadata.creationTimestamp
```

Depending on your KFP installation, step pods may run in the `kubeflow` namespace or another workflow namespace.

Look for names related to:

```text
failing-pipeline
failing-step
```

You can also inspect recent events:

```bash
kubectl get events -A --sort-by=.lastTimestamp
```

## Inspect Logs from Kubernetes

Once you find the pod:

```bash
kubectl logs -n <namespace> <pod-name>
```

For multi-container pods, list containers:

```bash
kubectl get pod -n <namespace> <pod-name> -o jsonpath='{.spec.containers[*].name}'
echo
```

Then choose a container:

```bash
kubectl logs -n <namespace> <pod-name> -c <container-name>
```

## Describe the Pod

```bash
kubectl describe pod -n <namespace> <pod-name>
```

Look for:

- container state
- exit code
- reason
- events
- image
- environment variables
- mounted volumes

## Common KFP Failure Modes

### Component code raises an exception

Symptoms:

- step failed
- logs show Python traceback

Debug:

```bash
kubectl logs -n <namespace> <pod-name>
```

### Image cannot be pulled

Symptoms:

```text
ImagePullBackOff
ErrImagePull
```

Debug:

```bash
kubectl describe pod -n <namespace> <pod-name>
```

Typical causes:

- wrong image tag
- image only exists locally but was not loaded into the active local cluster
- private registry credentials missing
- network or registry issue

### Missing Python package

Symptoms:

```text
ModuleNotFoundError
ImportError
```

Typical causes:

- dependency installed locally but not in component image
- lightweight component uses a base image that lacks the package
- project package not included in image

### Missing file or artifact

Symptoms:

```text
FileNotFoundError
```

Typical causes:

- using local filesystem assumptions
- reading from the wrong artifact path
- forgetting to write an output artifact
- treating artifact path as a file when it is a directory

### Pod pending

Symptoms:

```text
Pending
```

Debug:

```bash
kubectl describe pod -n <namespace> <pod-name>
kubectl get events -A --sort-by=.lastTimestamp
```

Typical causes:

- insufficient CPU
- insufficient memory
- insufficient GPU
- PVC cannot bind
- node selector or toleration mismatch

## KFP Debugging Checklist

When a KFP run fails:

1. Open the failed run in the KFP UI.
2. Identify the failed step.
3. Read the step logs in the UI.
4. List Kubernetes pods.
5. Find the pod for the failed step.
6. Run `kubectl logs`.
7. Run `kubectl describe pod`.
8. Check events.
9. Fix the component code, image, resources, or inputs.
10. Recompile and rerun.

Useful commands:

```bash
kubectl get pods -A --sort-by=.metadata.creationTimestamp
kubectl get events -A --sort-by=.lastTimestamp
kubectl describe pod -n <namespace> <pod-name>
kubectl logs -n <namespace> <pod-name>
```

## Cleanup

You can delete the failed run from the UI.

No Kubernetes cleanup is usually needed because completed or failed workflow pods may be managed by KFP/Argo cleanup behavior depending on the installation.

If you need to manually inspect or delete pods, be careful not to remove KFP system pods.

## What You Learned

You connected KFP-level failure information to Kubernetes-level debugging.

That is the main operational skill needed before moving into real training components.

## References

- [Run a pipeline](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/run-a-pipeline/)
- [Kubernetes debugging applications](https://kubernetes.io/docs/tasks/debug/debug-application/)
- [Kubernetes Pods](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Kubernetes events](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)

## Acceptance Criteria

You are done when:

- the failing pipeline compiles
- the failing pipeline run fails as expected
- you can find the failed step in the KFP UI
- you can find the corresponding Kubernetes pod
- you can inspect pod logs with `kubectl`
- you can explain whether the failure came from Python code, image setup, scheduling, or runtime configuration

## Next Step

Continue with Chapter 3: Local ML Workflow.
