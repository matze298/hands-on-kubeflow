"""Evaluate model pipeline component."""

from kfp.dsl import Input, Metrics, Model, Output
from kfp.dsl.component_decorator import component


@component(base_image="python:3.12-slim")
def evaluate_model(
    model: Input[Model],
    metrics: Output[Metrics],
) -> None:
    """Evaluates the model."""
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    model_path: Path = Path(model.path) / "model.json"
    model_data = json.loads(model_path.read_text(encoding="utf-8"))

    # Fake metric for now.
    accuracy = 0.90 if model_data["n_samples"] >= 50 else 0.70  # noqa: PLR2004

    metrics.log_metric("accuracy", accuracy)
    metrics.log_metric("n_samples", model_data["n_samples"])
