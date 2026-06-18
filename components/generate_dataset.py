"""Generate dataset pipeline component."""

from kfp.dsl import Dataset, Output
from kfp.dsl.component_decorator import component


@component(base_image="python:3.12-slim")
def generate_dataset(dataset: Output[Dataset], n_samples: int = 100) -> None:
    """Generates a dataset."""
    import json
    import random
    from pathlib import Path

    path = Path(dataset.path)
    path.mkdir(parents=True, exist_ok=True)

    samples = [{"x": random.random(), "y": random.randint(0, 1)} for _ in range(n_samples)]  # noqa: S311

    (path / "data.json").write_text(json.dumps(samples), encoding="utf-8")
