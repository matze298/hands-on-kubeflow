"""Tests for the evaluation module."""

import json
from typing import TYPE_CHECKING

from kubeflow_by_doing.evaluate import evaluate
from kubeflow_by_doing.train import train

if TYPE_CHECKING:
    from pathlib import Path


def test_evaluate_writes_metrics(tmp_path: Path) -> None:
    """Tests that the evaluation writes the metrics file."""
    model_dir = tmp_path / "model"
    metrics_path = tmp_path / "metrics.json"

    train(
        output_dir=model_dir,
        epochs=1,
        learning_rate=1e-3,
        seed=42,
        device="cpu",
        n_train=32,
        n_val=16,
        batch_size=8,
    )

    metrics = evaluate(
        model_dir=model_dir,
        metrics_path=metrics_path,
        seed=42,
        device="cpu",
        n_train=32,
        n_val=16,
        batch_size=8,
    )

    assert metrics_path.exists()
    assert 0.0 <= float(metrics["accuracy"]) <= 1.0

    loaded_metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert "accuracy" in loaded_metrics
    assert loaded_metrics["n_total"] == 16
