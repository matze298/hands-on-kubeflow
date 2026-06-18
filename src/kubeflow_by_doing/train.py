"""The training loop."""

import json
import random
from typing import TYPE_CHECKING, Any

import torch
from torch import nn
from torch.optim import Adam

from kubeflow_by_doing.data import DatasetConfig, make_dataloaders
from kubeflow_by_doing.model import TinyImageClassifier
from kubeflow_by_doing.storage import ObjectStorageConfig, ensure_bucket, run_prefix, upload_directory

if TYPE_CHECKING:
    from pathlib import Path


def set_seed(seed: int) -> None:
    """Fixes the seed for reproducibility."""
    random.seed(seed)
    torch.manual_seed(seed)


def select_device(device: str) -> torch.device:
    """Selects which device to train on.

    Returns:
        The selected device.

    Raises:
        RuntimeError: If CUDA is requested but not available.
    """
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is false")
    return torch.device(device)


def train(  # noqa:PLR0913
    *,
    output_dir: Path,
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    device: str = "auto",
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
    run_id: str | None = None,
    upload_artifacts: bool = False,
) -> dict[str, float | int | str | list[str]]:
    """Trains the model.

    Returns:
        The training summary.

    Raises:
        ValueError: If epochs or learning_rate are negative.
    """
    if epochs <= 0:
        raise ValueError("epochs must be positive")

    set_seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    torch_device = select_device(device)
    config = DatasetConfig(n_train=n_train, n_val=n_val, batch_size=batch_size, seed=seed)
    train_loader, _ = make_dataloaders(config)
    model = TinyImageClassifier(image_size=config.image_size, n_classes=config.n_classes).to(torch_device)

    loss_fn = nn.CrossEntropyLoss()
    optimizer = Adam(model.parameters(), lr=learning_rate)
    last_loss = 0.0

    model.train()
    for _epoch in range(epochs):
        for images, labels in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(images.to(torch_device))
            loss = loss_fn(logits, labels.to(torch_device))
            loss.backward()
            optimizer.step()
            last_loss = float(loss.detach().cpu().item())

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "image_size": config.image_size,
            "n_classes": config.n_classes,
            "seed": seed,
        },
        output_dir / "model.pt",
    )

    summary: dict[str, Any] = {
        "epochs": epochs,
        "learning_rate": learning_rate,
        "seed": seed,
        "n_train": n_train,
        "n_val": n_val,
        "batch_size": batch_size,
        "device": str(torch_device),
        "last_train_loss": last_loss,
    }

    if upload_artifacts:
        if run_id is None:
            msg = "run_id is required when upload_artifacts=True"
            raise ValueError(msg)

        storage_config = ObjectStorageConfig.from_env()
        ensure_bucket(storage_config)

        prefix = f"{run_prefix(run_id)}/models"

        uploaded_uris = upload_directory(local_dir=output_dir, prefix=prefix, config=storage_config)

        summary["model_artifact_prefix"] = f"s3://{storage_config.bucket}/{prefix}"
        summary["uploaded_artifacts"] = uploaded_uris

    # Dump summary
    (output_dir / "train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    return summary
