"""Evaluates the model."""

import json
from typing import TYPE_CHECKING

import torch

from kubeflow_by_doing.data import DatasetConfig, make_dataloaders
from kubeflow_by_doing.model import TinyImageClassifier
from kubeflow_by_doing.train import select_device, set_seed

if TYPE_CHECKING:
    from pathlib import Path


def evaluate(  # noqa:PLR0913
    *,
    model_dir: Path,
    metrics_path: Path,
    seed: int = 42,
    device: str = "auto",
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> dict[str, float | int | str]:
    """Evaluates a trained model.

    Returns:
        The evaluation metrics.

    Raises:
        FileNotFoundError: If the model artifact is not found.
    """
    set_seed(seed)

    model_path = model_dir / "model.pt"
    if not model_path.exists():
        msg = f"model artifact not found: {model_path}"
        raise FileNotFoundError(msg)

    torch_device = select_device(device)
    checkpoint = torch.load(model_path, map_location=torch_device)
    image_size = int(checkpoint["image_size"])
    n_classes = int(checkpoint["n_classes"])

    config = DatasetConfig(
        n_train=n_train,
        n_val=n_val,
        image_size=image_size,
        n_classes=n_classes,
        batch_size=batch_size,
        seed=seed,
    )
    _, val_loader = make_dataloaders(config)
    model = TinyImageClassifier(image_size=image_size, n_classes=n_classes).to(torch_device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    n_correct = 0
    n_total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            predictions = model(images.to(torch_device)).argmax(dim=1)
            n_correct += int((predictions == labels.to(torch_device)).sum().item())
            n_total += int(labels.to(torch_device).numel())

    accuracy = n_correct / n_total if n_total else 0.0
    metrics: dict[str, float | int | str] = {
        "accuracy": accuracy,
        "n_correct": n_correct,
        "n_total": n_total,
        "device": str(torch_device),
    }
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics
