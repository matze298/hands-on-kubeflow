"""Defines the TinyImageClassifier model."""

from typing import override

import torch
from torch import nn


class TinyImageClassifier(nn.Module):
    """TinyImageClassifier model."""

    def __init__(self, *, image_size: int = 16, n_classes: int = 2) -> None:
        """Initialize the model."""
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

    @override
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Returns:
            The class logits.
        """
        return self.classifier(self.features(x))
