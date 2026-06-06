"""Defines a failing pipeline."""

from kfp import compiler
from kfp.dsl.component_decorator import component
from kfp.dsl.pipeline_context import pipeline


@component(base_image="python:3.12-slim")
def start_step() -> str:
    """Starts the pipeline.

    Returns:
        The data URI.
    """
    print("start step succeeded")  # noqa: T201
    return "data-uri-placeholder"


@component(base_image="python:3.12-slim")
def failing_step(data_uri: str) -> None:
    """Failing step.

    Raises:
        RuntimeError: Simulated KFP component failure.
    """
    print(f"received {data_uri=}")  # noqa:T201
    raise RuntimeError("simulated KFP component failure")  # noqa: EM101, TRY003


@component(base_image="python:3.12-slim")
def never_runs() -> None:
    """Never runs step."""
    print("this should not run")  # noqa: T201


@pipeline(name="failing-pipeline")
def failing_pipeline() -> None:
    """Defines the failing pipeline."""
    start_task = start_step()
    failed_task = failing_step(data_uri=start_task.output)
    never_runs().after(failed_task)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=failing_pipeline,
        package_path="compiled/failing_pipeline.yaml",
    )
