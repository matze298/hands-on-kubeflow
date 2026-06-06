"""Defines a simple hello pipeline."""

from kfp import compiler
from kfp.dsl.component_decorator import component
from kfp.dsl.pipeline_context import pipeline


@component(base_image="python:3.12-slim")
def create_message(name: str) -> str:
    """Create a message.

    Returns:
        The message.
    """
    return f"hello, {name}"


@component(base_image="python:3.12-slim")
def print_message(message: str) -> None:
    """Prints a message."""
    print(message)  # noqa:T201


@pipeline(name="hello-pipeline")
def hello_pipeline(name: str = "kubeflow") -> None:
    """Defines the pipeline."""
    message_task = create_message(name=name)
    print_message(message=message_task.output)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=hello_pipeline,
        package_path="compiled/hello_pipeline.yaml",
    )
