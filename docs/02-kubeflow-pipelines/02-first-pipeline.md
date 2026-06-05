# First Pipeline

This page creates the smallest useful Kubeflow pipeline.

The pipeline does not train a model yet. It exists to teach the development loop:

```text
write pipeline code
  ↓
compile to YAML
  ↓
upload to KFP
  ↓
run
  ↓
inspect result
```

## What You Will Build

You will build a two-step pipeline:

```text
create_message → print_message
```

## Why This Matters

A Kubeflow pipeline is not just a Python script.

The Python code defines a workflow. The KFP compiler turns that workflow into a pipeline specification. The KFP backend then executes that specification as Kubernetes workloads.

## Create the Pipeline File

Create:

```bash
mkdir -p pipelines compiled
```

Create `pipelines/hello_pipeline.py`:

```python
from kfp import compiler, dsl


@dsl.component(base_image="python:3.12-slim")
def create_message(name: str) -> str:
    return f"hello, {name}"


@dsl.component(base_image="python:3.12-slim")
def print_message(message: str) -> None:
    print(message)


@dsl.pipeline(name="hello-pipeline")
def hello_pipeline(name: str = "kubeflow") -> None:
    message_task = create_message(name=name)
    print_message(message=message_task.output)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=hello_pipeline,
        package_path="compiled/hello_pipeline.yaml",
    )
```

## Compile the Pipeline

Run:

```bash
uv run python pipelines/hello_pipeline.py
```

Verify:

```bash
ls -lh compiled/hello_pipeline.yaml
```

You should see a compiled YAML file.

## Inspect the Compiled YAML

Open the file:

```bash
head -n 40 compiled/hello_pipeline.yaml
```

You do not need to understand every line.

The important point is:

```text
Python DSL code became a portable pipeline specification.
```

## Upload the Pipeline in the UI

Start port forwarding if it is not already running:

```bash
kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8080:80
```

Open:

```text
http://localhost:8080
```

Then:

1. go to **Pipelines**
2. click **Upload pipeline**
3. upload `compiled/hello_pipeline.yaml`
4. name it `hello-pipeline`
5. create a run
6. set `name` to your name or `kubeflow`
7. start the run

## Inspect the Run

In the KFP UI:

1. open the run
2. inspect the graph
3. click each step
4. inspect logs and outputs

You should see:

```text
hello, kubeflow
```

or your chosen name.

## What Happened?

The Python functions decorated with `@dsl.component` became pipeline components.

The function decorated with `@dsl.pipeline` composed those components into a workflow.

The KFP compiler produced the YAML specification.

The KFP backend executed the steps in Kubernetes.

## Common Problems

### `ModuleNotFoundError: No module named 'kfp'`

Install the KFP SDK:

```bash
uv add kfp
```

Then retry:

```bash
uv run python pipelines/hello_pipeline.py
```

### The UI cannot upload the pipeline

Check that the compiled file exists:

```bash
ls -lh compiled/hello_pipeline.yaml
```

Check that KFP is running:

```bash
kubectl get pods -n kubeflow
```

### The run fails

Open the failed step in the KFP UI and inspect logs.

Then check Kubernetes:

```bash
kubectl get pods -n kubeflow
kubectl get pods -A | grep hello || true
```

Depending on the KFP backend and namespace setup, pipeline step pods may appear in a workflow namespace or the KFP namespace.

## Cleanup

No cleanup is required.

You can delete the run or pipeline from the UI if you want a clean workspace.

## What You Learned

You created, compiled, uploaded, and ran your first Kubeflow pipeline.

You also saw the core KFP development loop:

```text
Python DSL → compiled YAML → pipeline run → Kubernetes execution
```

## References

- [Kubeflow Pipelines getting started](https://www.kubeflow.org/docs/components/pipelines/getting-started/)
- [Compile a pipeline](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/compile-a-pipeline/)
- [Run a pipeline](https://www.kubeflow.org/docs/components/pipelines/user-guides/core-functions/run-a-pipeline/)
- [KFP SDK reference](https://www.kubeflow.org/docs/components/pipelines/reference/sdk/)

## Acceptance Criteria

You are done when:

- `compiled/hello_pipeline.yaml` exists
- the pipeline can be uploaded in the KFP UI
- a run completes successfully
- the `print_message` step logs the expected message

## Next Step

Continue with [Run a Pipeline from Python](03-run-pipeline-from-python.md).
