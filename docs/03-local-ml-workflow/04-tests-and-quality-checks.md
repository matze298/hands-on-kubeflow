# Tests and Quality Checks

This page adds local validation before containerizing the training workflow.

## What You Will Build

Create tests for:

```text
tests/test_data.py
tests/test_train.py
tests/test_evaluate.py
```

Then run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

## Why This Matters

Kubernetes is a slow place to discover simple Python mistakes.

The local quality gate should catch:

- import errors
- broken CLI wiring
- missing output files
- invalid metrics JSON
- obvious type errors
- formatting and linting issues

before you build an image or run Kubeflow.

## Test the Dataset Code

Create `tests/test_data.py`:

```python
from __future__ import annotations

import torch

from kubeflow_by_doing.data import DatasetConfig, make_dataloaders, make_synthetic_images


def test_synthetic_images_are_deterministic() -> None:
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
    config = DatasetConfig(n_train=16, n_val=8, image_size=16, n_classes=2, batch_size=4, seed=42)
    train_loader, val_loader = make_dataloaders(config)
    train_images, train_labels = next(iter(train_loader))
    val_images, val_labels = next(iter(val_loader))

    assert train_images.shape == (4, 1, 16, 16)
    assert train_labels.shape == (4,)
    assert val_images.shape == (4, 1, 16, 16)
    assert val_labels.shape == (4,)
```

## Test Training

Create `tests/test_train.py`:

```python
from __future__ import annotations

import json

from kubeflow_by_doing.train import train


def test_train_writes_model_and_summary(tmp_path) -> None:
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
```

Use `tmp_path` so tests do not write into the repository.

## Test Evaluation

Create `tests/test_evaluate.py`:

```python
from __future__ import annotations

import json

from kubeflow_by_doing.evaluate import evaluate
from kubeflow_by_doing.train import train


def test_evaluate_writes_metrics(tmp_path) -> None:
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
```

## Run Tests

```bash
uv run pytest
```

For concise output:

```bash
uv run pytest -q
```

## Run Ruff

```bash
uv run ruff format --check .
uv run ruff check .
```

Apply safe fixes if needed:

```bash
uv run ruff format .
uv run ruff check . --fix
```

## Run ty

```bash
uv run ty check
```

`ty` should help catch type-related mistakes without turning the tutorial into a type-system deep dive.

## Optional Local Check Command

If the repo already uses a `Makefile`:

```makefile
.PHONY: check
check:
	uv run ruff format --check .
	uv run ruff check .
	uv run ty check
	uv run pytest
```

If the repo does not already use a `Makefile`, do not add one just for this chapter. Running the `uv run` commands directly is enough.

## Common Problems

### Tests write into the repo

Use `tmp_path`.

Tests should not create persistent outputs unless the test is explicitly about a repository artifact.

### Tests are slow

Reduce the dataset size and epochs used in tests.

A test training run should be a smoke test, not a real experiment.

### Type checker complains about third-party libraries

Keep type annotations on tutorial-owned code. Avoid spending too much tutorial space on third-party typing issues.

## Cleanup

If tests accidentally created outputs:

```bash
rm -rf outputs/
```

## Acceptance Criteria

You are done when:

- data tests exist
- training tests exist
- evaluation tests exist
- `uv run pytest` passes
- `uv run ruff format --check .` passes
- `uv run ruff check .` passes
- `uv run ty check` passes or has a documented temporary exception
- you can run the full local quality gate from the repo root

## References

- [pytest documentation](https://docs.pytest.org/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [ty documentation](https://docs.astral.sh/ty/)

## Next Step

Continue with [Containerize Training](05-containerize-training.md).
