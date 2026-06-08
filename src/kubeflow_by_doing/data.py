"""Synthetic image classification dataset."""

from dataclasses import dataclass

import torch
from torch.utils.data import DataLoader, TensorDataset


@dataclass(frozen=True)
class DatasetConfig:
    """Dataset configuration."""

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
    min_num_classes: int = 2,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Create the synthetic images and labels.

    Returns:
        Tuple of images and labels.

    Raises:
        ValueError: If n_samples or image_size are negative.
        ValueError: If n_classes is less than 2.
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    if image_size <= 0:
        raise ValueError("image_size must be positive")
    if n_classes < min_num_classes:
        raise ValueError("n_classes must be at least 2")

    generator = torch.Generator().manual_seed(seed)
    labels = torch.randint(0, n_classes, (n_samples,), generator=generator)
    noise = torch.randn(n_samples, 1, image_size, image_size, generator=generator)
    offsets = labels.float().view(n_samples, 1, 1, 1) / float(n_classes - 1)
    images = noise * 0.25 + offsets
    return images.float(), labels.long()


def make_dataloaders(config: DatasetConfig) -> tuple[DataLoader, DataLoader]:
    """Create the training and validation dataloaders.

    Returns:
        Tuple of training and validation dataloaders.
    """
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
