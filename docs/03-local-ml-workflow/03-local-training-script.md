# Local Training Script

This page creates the local training workflow.

The model remains intentionally simple. The purpose is to create a clean training entrypoint that can later run inside a container and then inside Kubeflow.

## What You Will Build

Create:

```text
src/kubeflow_by_doing/__init__.py
src/kubeflow_by_doing/data.py
src/kubeflow_by_doing/model.py
src/kubeflow_by_doing/train.py
src/kubeflow_by_doing/evaluate.py
src/kubeflow_by_doing/cli.py
```

The CLI should support commands like:

```bash
uv run kbd train-model --output-dir outputs/local-train --epochs 2 --device auto
uv run kbd evaluate-model --model-dir outputs/local-train --metrics-path outputs/local-train/metrics.json --device auto
```

## Why This Matters

The local script gives us a fast feedback loop:

```text
edit Python
  ↓
run locally
  ↓
test locally
  ↓
containerize
  ↓
run in Kubernetes
  ↓
run in Kubeflow
```

If the script fails locally, Kubeflow cannot fix it.

## Design Rules

Keep the training code:

- deterministic enough for tests
- small enough to run quickly
- configurable through CLI arguments
- able to write model artifacts to a chosen output directory
- able to write metrics to a chosen path
- independent of Kubeflow

Avoid:

- hardcoded absolute paths
- hidden local files
- notebook-only logic
- importing from `components/` or `pipelines/`
- relying on the current working directory

## Package Scaffold

Create `src/kubeflow_by_doing/__init__.py`:

```python
"""Local-first Kubeflow tutorial package."""

__all__ = ["__version__"]

__version__ = "0.1.0"
```

## `data.py`

Synthetic data is enough for the first implementation. It avoids flaky downloads and keeps the tutorial local-first.

Create `src/kubeflow_by_doing/data.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.utils.data import DataLoader, TensorDataset


@dataclass(frozen=True)
class DatasetConfig:
    n_train: int = 256
    n_val: int = 64
    image_size: int = 16
    n_classes: int = 2
    batch_size: int = 32
    seed: int = 42


def make_synthetic_images(
    *,
    n_samples: int,
    image_size: int,
    n_classes: int,
    seed: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    if image_size <= 0:
        raise ValueError("image_size must be positive")
    if n_classes < 2:
        raise ValueError("n_classes must be at least 2")

    generator = torch.Generator().manual_seed(seed)
    labels = torch.randint(0, n_classes, (n_samples,), generator=generator)
    noise = torch.randn(n_samples, 1, image_size, image_size, generator=generator)
    offsets = labels.float().view(n_samples, 1, 1, 1) / float(n_classes - 1)
    images = noise * 0.25 + offsets
    return images.float(), labels.long()


def make_dataloaders(config: DatasetConfig) -> tuple[DataLoader, DataLoader]:
    train_images, train_labels = make_synthetic_images(
        n_samples=config.n_train,
        image_size=config.image_size,
        n_classes=config.n_classes,
        seed=config.seed,
    )
    val_images, val_labels = make_synthetic_images(
        n_samples=config.n_val,
        image_size=config.image_size,
        n_classes=config.n_classes,
        seed=config.seed + 1,
    )

    train_loader = DataLoader(
        TensorDataset(train_images, train_labels),
        batch_size=config.batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(config.seed),
    )
    val_loader = DataLoader(
        TensorDataset(val_images, val_labels),
        batch_size=config.batch_size,
        shuffle=False,
    )
    return train_loader, val_loader
```

## `model.py`

Create `src/kubeflow_by_doing/model.py`:

```python
from __future__ import annotations

import torch
from torch import nn


class TinyImageClassifier(nn.Module):
    def __init__(self, *, image_size: int = 16, n_classes: int = 2) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 8, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(8 * 4 * 4, n_classes),
        )
        self.image_size = image_size
        self.n_classes = n_classes

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))
```

## `train.py`

Target output:

```text
output_dir/
├── model.pt
└── train_summary.json
```

Create `src/kubeflow_by_doing/train.py`:

```python
from __future__ import annotations

import json
import random
from pathlib import Path

import torch
from torch import nn
from torch.optim import Adam

from kubeflow_by_doing.data import DatasetConfig, make_dataloaders
from kubeflow_by_doing.model import TinyImageClassifier


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def select_device(device: str) -> torch.device:
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is false")
    return torch.device(device)


def train(
    *,
    output_dir: Path,
    epochs: int = 2,
    learning_rate: float = 1e-3,
    seed: int = 42,
    device: str = "auto",
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> dict[str, float | int | str]:
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
            images = images.to(torch_device)
            labels = labels.to(torch_device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = loss_fn(logits, labels)
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

    summary: dict[str, float | int | str] = {
        "epochs": epochs,
        "learning_rate": learning_rate,
        "seed": seed,
        "n_train": n_train,
        "n_val": n_val,
        "batch_size": batch_size,
        "device": str(torch_device),
        "last_train_loss": last_loss,
    }
    (output_dir / "train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
```

## `evaluate.py`

Target metric shape:

```json
{
  "accuracy": 0.91,
  "n_total": 64
}
```

Create `src/kubeflow_by_doing/evaluate.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import torch

from kubeflow_by_doing.data import DatasetConfig, make_dataloaders
from kubeflow_by_doing.model import TinyImageClassifier
from kubeflow_by_doing.train import select_device, set_seed


def evaluate(
    *,
    model_dir: Path,
    metrics_path: Path,
    seed: int = 42,
    device: str = "auto",
    n_train: int = 256,
    n_val: int = 64,
    batch_size: int = 32,
) -> dict[str, float | int | str]:
    set_seed(seed)

    model_path = model_dir / "model.pt"
    if not model_path.exists():
        raise FileNotFoundError(f"model artifact not found: {model_path}")

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
            images = images.to(torch_device)
            labels = labels.to(torch_device)
            predictions = model(images).argmax(dim=1)
            n_correct += int((predictions == labels).sum().item())
            n_total += int(labels.numel())

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
```

## `cli.py`

Use `typer` for a thin CLI. The CLI should call package functions. It should not contain the training implementation.

Create `src/kubeflow_by_doing/cli.py`:

```python
from __future__ import annotations

from pathlib import Path

import typer
from rich import print as rprint

from kubeflow_by_doing.evaluate import evaluate
from kubeflow_by_doing.train import train

app = typer.Typer(no_args_is_help=True, help="Local-first Kubeflow tutorial CLI.")


@app.command()
def train_model(
    output_dir: Path = typer.Option(..., help="Directory for model artifacts."),
    epochs: int = typer.Option(2, help="Number of training epochs."),
    learning_rate: float = typer.Option(1e-3, help="Optimizer learning rate."),
    seed: int = typer.Option(42, help="Random seed."),
    device: str = typer.Option("auto", help="Device: auto, cpu, or cuda."),
    n_train: int = typer.Option(256, help="Number of synthetic training samples."),
    n_val: int = typer.Option(64, help="Number of synthetic validation samples."),
    batch_size: int = typer.Option(32, help="Batch size."),
) -> None:
    rprint(
        train(
            output_dir=output_dir,
            epochs=epochs,
            learning_rate=learning_rate,
            seed=seed,
            device=device,
            n_train=n_train,
            n_val=n_val,
            batch_size=batch_size,
        )
    )


@app.command()
def evaluate_model(
    model_dir: Path = typer.Option(..., help="Directory containing model.pt."),
    metrics_path: Path = typer.Option(..., help="Path to write metrics JSON."),
    seed: int = typer.Option(42, help="Random seed."),
    device: str = typer.Option("auto", help="Device: auto, cpu, or cuda."),
    n_train: int = typer.Option(256, help="Number of synthetic training samples."),
    n_val: int = typer.Option(64, help="Number of synthetic validation samples."),
    batch_size: int = typer.Option(32, help="Batch size."),
) -> None:
    rprint(
        evaluate(
            model_dir=model_dir,
            metrics_path=metrics_path,
            seed=seed,
            device=device,
            n_train=n_train,
            n_val=n_val,
            batch_size=batch_size,
        )
    )


if __name__ == "__main__":
    app()
```

## Run Local Training

```bash
mkdir -p outputs/local-train

uv run kbd train-model \
  --output-dir outputs/local-train \
  --epochs 2 \
  --learning-rate 0.001 \
  --seed 42 \
  --device auto
```

Verify:

```bash
ls -lh outputs/local-train
```

Expected:

```text
model.pt
train_summary.json
```

## Run Local Evaluation

```bash
uv run kbd evaluate-model \
  --model-dir outputs/local-train \
  --metrics-path outputs/local-train/metrics.json \
  --seed 42 \
  --device auto
```

Verify:

```bash
cat outputs/local-train/metrics.json
```

## Common Problems

### CLI command is not found

Check that `pyproject.toml` contains:

```toml
[project.scripts]
kbd = "kubeflow_by_doing.cli:app"
```

Then run:

```bash
uv sync
uv run kbd --help
```

### Import from `kubeflow_by_doing` fails

Check that:

- the project uses the `src/` layout
- `pyproject.toml` includes the needed configuration
- commands are run from the repository root

### Training is slow

Reduce dataset size, image size, epochs, or model size. The tutorial should run quickly.

## Cleanup

```bash
rm -rf outputs/local-train
```

Do not remove source files.

## Acceptance Criteria

You are done when:

- `uv run kbd --help` works
- `uv run kbd train-model ...` writes `model.pt`
- `uv run kbd train-model ...` writes `train_summary.json`
- `uv run kbd evaluate-model ...` writes `metrics.json`
- the training and evaluation functions do not import from `components/` or `pipelines/`

## References

- [PyTorch tutorials](https://pytorch.org/tutorials/)
- [Typer documentation](https://typer.tiangolo.com/)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html)

## Next Step

Continue with [Tests and Quality Checks](04-tests-and-quality-checks.md).
