"""Tests the training module."""

import json
from typing import TYPE_CHECKING

from kubeflow_by_doing.train import train

if TYPE_CHECKING:
    from pathlib import Path


def test_train_writes_model_and_summary(tmp_path: Path) -> None:
    """Tests that the training writes the model and summary files."""
    summary = train(
        output_dir=tmp_path,
        epochs=1,
        learning_rate=1e-3,
        seed=42,
        device="cpu",
        n_train=32,
        n_val=16,
        batch_size=8,
    )

    model_path = tmp_path / "model.pt"
    summary_path = tmp_path / "train_summary.json"

    assert model_path.exists()
    assert summary_path.exists()
    assert summary["epochs"] == 1

    loaded_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded_summary["n_train"] == 32
    assert loaded_summary["n_val"] == 16
