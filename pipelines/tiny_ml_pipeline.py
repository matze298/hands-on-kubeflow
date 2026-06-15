"""Refactored TinyML pipeline."""

from kfp import compiler
from kfp.dsl import Dataset, Input, Metrics, Model, Output  # noqa: TC002
from kfp.dsl.component_decorator import component
from kfp.dsl.pipeline_context import pipeline


@component(base_image="python:3.12-slim")
def generate_dataset(dataset: Output[Dataset], n_samples: int = 100) -> None:
    """Generates a dataset."""
    import json  # noqa: PLC0415
    import random  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    path = Path(dataset.path)
    path.mkdir(parents=True, exist_ok=True)

    samples = [{"x": random.random(), "y": random.randint(0, 1)} for _ in range(n_samples)]  # noqa:S311

    (path / "data.json").write_text(json.dumps(samples), encoding="utf-8")


@component(base_image="python:3.12-slim")
def train_model(
    dataset: Input[Dataset],
    model: Output[Model],
    learning_rate: float = 0.01,
) -> None:
    """Trains a model."""
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    data_path = Path(dataset.path) / "data.json"
    samples = json.loads(data_path.read_text(encoding="utf-8"))

    model_path = Path(model.path)
    model_path.mkdir(parents=True, exist_ok=True)

    # This is intentionally not real ML yet.
    # The point is to create a model artifact.
    artifact = {
        "kind": "tiny-threshold-model",
        "learning_rate": learning_rate,
        "n_samples": len(samples),
        "threshold": 0.5,
    }

    (model_path / "model.json").write_text(json.dumps(artifact), encoding="utf-8")


@component(base_image="python:3.12-slim")
def evaluate_model(
    model: Input[Model],
    metrics: Output[Metrics],
) -> None:
    """Evaluates the model."""
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    model_path = Path(model.path) / "model.json"
    model_data = json.loads(model_path.read_text(encoding="utf-8"))

    # Fake metric for now.
    accuracy = 0.90 if model_data["n_samples"] >= 50 else 0.70  # noqa: PLR2004

    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("n_samples", model_data["n_samples"])


@pipeline(name="tiny-ml-pipeline")
def tiny_ml_pipeline(
    n_samples: int = 100,
    learning_rate: float = 0.01,
) -> None:
    """Defines the TinyML pipeline."""
    dataset_task = generate_dataset(n_samples=n_samples)
    model_task = train_model(
        dataset=dataset_task.outputs["dataset"],
        learning_rate=learning_rate,
    )
    evaluate_model(model=model_task.outputs["model"])


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=tiny_ml_pipeline,
        package_path="compiled/tiny_ml_pipeline.yaml",
    )
