"""Generate dataset pipeline component."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kfp.dsl import Dataset, Output
from kfp.dsl.component_decorator import component


@component(base_image="python:3.12-slim")
def generate_dataset(dataset: Output[Dataset], n_samples: int = 100) -> None:
    """Generates a dataset."""
    import json  # noqa: PLC0415
    import random  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    path = Path(dataset.path)
    path.mkdir(parents=True, exist_ok=True)

    samples = [{"x": random.random(), "y": random.randint(0, 1)} for _ in range(n_samples)]  # noqa: S311

    (path / "data.json").write_text(json.dumps(samples), encoding="utf-8")
