"""Promote a model given a threshold."""

from typing import Any

from kfp.dsl import Artifact, Input, Model, Output
from kfp.dsl.component_decorator import component


@component(base_image="python:3.12-slim")
def read_accuracy(metrics: Input[Artifact]) -> float:
    """Read the accuracy from a metrics artifact.

    Args:
        metrics: Metrics artifact written by the evaluation component.

    Returns:
        The accuracy.
    """
    import json
    from pathlib import Path

    metrics_data: dict[str, Any] = json.loads(Path(metrics.path).read_text("utf-8"))
    return float(metrics_data.get("accuracy", 0))


@component(base_image="python:3.12-slim")
def promote_model(
    model: Input[Model],
    promotion: Output[Artifact],
    accuracy: float,
    min_accuracy: float = 0.8,
) -> None:
    """Write a promotion artifact when a model clears the accuracy gate.

    Args:
        model: Trained model artifact produced by the training component.
        promotion: Output artifact that records the promotion decision.
        accuracy: Evaluation accuracy for the trained model.
        min_accuracy: Minimum accuracy required before the model is promoted.
    """
    import json
    from pathlib import Path

    promotion_path = Path(promotion.path)
    promotion_path.parent.mkdir(parents=True, exist_ok=True)
    promotion_path.write_text(
        json.dumps(
            {
                "status": "promoted",
                "accuracy": accuracy,
                "min_accuracy": min_accuracy,
                "model_uri": model.uri,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
