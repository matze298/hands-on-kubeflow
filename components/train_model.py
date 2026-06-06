"""Train model pipeline component."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kfp.dsl import Dataset, Input, Model, Output
from kfp.dsl.component_decorator import component


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
