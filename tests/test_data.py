"""Tests for the data module."""

import torch

from kubeflow_by_doing.data import DatasetConfig, make_dataloaders, make_synthetic_images


def test_synthetic_images_are_deterministic() -> None:
    """Tests that the synthetic images are created deterministically."""
    images_a, labels_a = make_synthetic_images(
        n_samples=8,
        image_size=16,
        n_classes=2,
        seed=42,
    )
    images_b, labels_b = make_synthetic_images(
        n_samples=8,
        image_size=16,
        n_classes=2,
        seed=42,
    )

    assert torch.equal(images_a, images_b)
    assert torch.equal(labels_a, labels_b)


def test_dataloaders_have_expected_shapes() -> None:
    """Tests that the dataloaders have the expected shapes."""
    config = DatasetConfig(n_train=16, n_val=8, image_size=16, n_classes=2, batch_size=4, seed=42)
    train_loader, val_loader = make_dataloaders(config)
    train_images, train_labels = next(iter(train_loader))
    val_images, val_labels = next(iter(val_loader))

    assert train_images.shape == (4, 1, 16, 16)
    assert train_labels.shape == (4,)
    assert val_images.shape == (4, 1, 16, 16)
    assert val_labels.shape == (4,)
