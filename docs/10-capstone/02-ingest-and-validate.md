# Ingest and Validate

This page adds the first two capstone steps:

```text
ingest_data
  ↓
validate_data
```

## What You Will Build

You will create:

```text
src/kubeflow_by_doing/ingest.py
src/kubeflow_by_doing/validate.py
components/ingest_data.py
components/validate_data.py
tests/test_ingest.py
tests/test_validate.py
```

## Why This Matters

The earlier pipeline generated data implicitly inside training.

The capstone makes data explicit:

```text
dataset manifest
  ↓
validation report
  ↓
training input
```

Even for synthetic data, this teaches the platform shape.

## Create `ingest.py`

Create `src/kubeflow_by_doing/ingest.py` yourself first.

Requirements:

- expose an `ingest_data(...)` function
- write a JSON dataset manifest to the requested output path
- include `dataset_uri`, `run_id`, `n_train`, `n_val`, `image_size`, `n_classes`, and whether the dataset is synthetic
- optionally upload the manifest to the Chapter 4 object-storage layout under `datasets/`
- return the manifest dictionary

Hint: reuse `ObjectStorageConfig`, `ensure_bucket`, `run_prefix`, and `upload_file` from the artifact chapter.

??? example "Reference implementation: `src/kubeflow_by_doing/ingest.py`"

    ```python
    from __future__ import annotations

    import json
    from pathlib import Path

    from kubeflow_by_doing.storage import (
        ObjectStorageConfig,
        ensure_bucket,
        run_prefix,
        upload_file,
    )


    def ingest_data(
        *,
        output_path: Path,
        run_id: str,
        dataset_uri: str,
        n_train: int,
        n_val: int,
        image_size: int,
        n_classes: int,
        upload_artifacts: bool = False,
    ) -> dict[str, str | int | bool]:
        """Create a dataset manifest for the tutorial dataset."""
        manifest: dict[str, str | int | bool] = {
            "dataset_uri": dataset_uri,
            "run_id": run_id,
            "n_train": n_train,
            "n_val": n_val,
            "image_size": image_size,
            "n_classes": n_classes,
            "synthetic": dataset_uri.startswith("synthetic://"),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        if upload_artifacts:
            config = ObjectStorageConfig.from_env()
            ensure_bucket(config)

            key = f"{run_prefix(run_id)}/datasets/dataset_manifest.json"
            manifest_uri = upload_file(local_path=output_path, key=key, config=config)
            manifest["manifest_uri"] = manifest_uri
            output_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return manifest
    ```

## Create `validate.py`

Create `src/kubeflow_by_doing/validate.py` yourself first.

Requirements:

- expose a `validate_data(...)` function
- load the dataset manifest JSON
- fail if required fields are missing or obviously invalid
- write a validation report JSON
- optionally upload the report under `validation/`
- return the report dictionary

Hint: keep the checks simple. The capstone is testing platform integration, not a full data-quality framework.

??? example "Reference implementation: `src/kubeflow_by_doing/validate.py`"

    ```python
    from __future__ import annotations

    import json
    from pathlib import Path

    from kubeflow_by_doing.storage import (
        ObjectStorageConfig,
        ensure_bucket,
        run_prefix,
        upload_file,
    )


    def validate_data(
        *,
        manifest_path: Path,
        report_path: Path,
        run_id: str,
        upload_artifacts: bool = False,
    ) -> dict[str, str | int | bool]:
        """Validate the dataset manifest and write a validation report."""
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        errors: list[str] = []

        if not manifest.get("dataset_uri"):
            errors.append("dataset_uri is required")
        if int(manifest.get("n_train", 0)) <= 0:
            errors.append("n_train must be positive")
        if int(manifest.get("n_val", 0)) <= 0:
            errors.append("n_val must be positive")
        if int(manifest.get("image_size", 0)) <= 0:
            errors.append("image_size must be positive")
        if int(manifest.get("n_classes", 0)) < 2:
            errors.append("n_classes must be at least 2")

        report: dict[str, str | int | bool] = {
            "run_id": run_id,
            "valid": not errors,
            "n_errors": len(errors),
            "errors": json.dumps(errors),
            "dataset_uri": str(manifest.get("dataset_uri", "")),
        }

        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        if errors:
            raise ValueError(f"dataset validation failed: {errors}")

        if upload_artifacts:
            config = ObjectStorageConfig.from_env()
            ensure_bucket(config)

            key = f"{run_prefix(run_id)}/validation/validation_report.json"
            report_uri = upload_file(local_path=report_path, key=key, config=config)
            report["report_uri"] = report_uri
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        return report
    ```

## Add CLI Commands

Update `src/kubeflow_by_doing/cli.py` yourself.

Requirements:

- add one command that calls `ingest_data(...)`
- add one command that calls `validate_data(...)`
- expose the paths and run ID as options
- expose `upload_artifacts` as a boolean option
- print the returned dictionary with the existing CLI output style

??? example "Reference implementation: CLI commands"

    ```python
    @app.command()
    def ingest_data_cmd(
        output_path: Path = typer.Option(..., help="Path to write dataset manifest."),
        run_id: str = typer.Option(..., help="Run ID."),
        dataset_uri: str = typer.Option("synthetic://tiny-image-classification"),
        n_train: int = typer.Option(256),
        n_val: int = typer.Option(64),
        image_size: int = typer.Option(16),
        n_classes: int = typer.Option(2),
        upload_artifacts: bool = typer.Option(False),
    ) -> None:
        from kubeflow_by_doing.ingest import ingest_data

        result = ingest_data(
            output_path=output_path,
            run_id=run_id,
            dataset_uri=dataset_uri,
            n_train=n_train,
            n_val=n_val,
            image_size=image_size,
            n_classes=n_classes,
            upload_artifacts=upload_artifacts,
        )
        rprint(result)


    @app.command()
    def validate_data_cmd(
        manifest_path: Path = typer.Option(...),
        report_path: Path = typer.Option(...),
        run_id: str = typer.Option(...),
        upload_artifacts: bool = typer.Option(False),
    ) -> None:
        from kubeflow_by_doing.validate import validate_data

        result = validate_data(
            manifest_path=manifest_path,
            report_path=report_path,
            run_id=run_id,
            upload_artifacts=upload_artifacts,
        )
        rprint(result)
    ```

!!! note

    Typer may expose command names with hyphens. Verify the final command names with `uv run kbd --help`, then keep the component args aligned with the CLI.

## Create `components/ingest_data.py`

Create this component yourself.

Requirements:

- define a `@dsl.container_component`
- output a `Dataset` artifact
- call the ingest CLI command inside the tutorial image
- pass run and dataset parameters through as component inputs
- append `--upload-artifacts` when enabled

??? example "Reference implementation: `components/ingest_data.py`"

    ```python
    from __future__ import annotations

    from kfp import dsl
    from kfp.dsl import Dataset, Output


    @dsl.container_component
    def ingest_data(
        dataset_manifest: Output[Dataset],
        image: str,
        run_id: str,
        dataset_uri: str = "synthetic://tiny-image-classification",
        n_train: int = 256,
        n_val: int = 64,
        image_size: int = 16,
        n_classes: int = 2,
        upload_artifacts: bool = True,
    ) -> dsl.ContainerSpec:
        args = [
            "ingest-data-cmd",
            "--output-path",
            dataset_manifest.path,
            "--run-id",
            run_id,
            "--dataset-uri",
            dataset_uri,
            "--n-train",
            n_train,
            "--n-val",
            n_val,
            "--image-size",
            image_size,
            "--n-classes",
            n_classes,
        ]

        if upload_artifacts:
            args.append("--upload-artifacts")

        return dsl.ContainerSpec(
            image=image,
            command=["kbd"],
            args=args,
        )
    ```

## Create `components/validate_data.py`

Create this component yourself.

Requirements:

- read the `Dataset` artifact from `ingest_data`
- write a validation report artifact
- call the validation CLI command inside the tutorial image
- append `--upload-artifacts` when enabled

??? example "Reference implementation: `components/validate_data.py`"

    ```python
    from __future__ import annotations

    from kfp import dsl
    from kfp.dsl import Dataset, Input, Output, Artifact


    @dsl.container_component
    def validate_data(
        dataset_manifest: Input[Dataset],
        validation_report: Output[Artifact],
        image: str,
        run_id: str,
        upload_artifacts: bool = True,
    ) -> dsl.ContainerSpec:
        args = [
            "validate-data-cmd",
            "--manifest-path",
            dataset_manifest.path,
            "--report-path",
            validation_report.path,
            "--run-id",
            run_id,
        ]

        if upload_artifacts:
            args.append("--upload-artifacts")

        return dsl.ContainerSpec(
            image=image,
            command=["kbd"],
            args=args,
        )
    ```

## Create Tests

Create tests yourself before opening the reference.

Required coverage:

- ingest writes the manifest file
- ingest returns the run ID and requested values
- validation accepts a valid manifest
- validation writes a report with zero errors
- validation rejects an invalid manifest

??? example "Reference implementation: `tests/test_ingest.py`"

    ```python
    from __future__ import annotations

    import json

    from kubeflow_by_doing.ingest import ingest_data


    def test_ingest_writes_manifest(tmp_path) -> None:
        output_path = tmp_path / "dataset_manifest.json"

        manifest = ingest_data(
            output_path=output_path,
            run_id="test-run",
            dataset_uri="synthetic://tiny-image-classification",
            n_train=32,
            n_val=16,
            image_size=16,
            n_classes=2,
        )

        assert output_path.exists()
        assert manifest["run_id"] == "test-run"

        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        assert loaded["n_train"] == 32
    ```

??? example "Reference implementation: `tests/test_validate.py`"

    ```python
    from __future__ import annotations

    import json
    import pytest

    from kubeflow_by_doing.ingest import ingest_data
    from kubeflow_by_doing.validate import validate_data


    def test_validate_accepts_valid_manifest(tmp_path) -> None:
        manifest_path = tmp_path / "dataset_manifest.json"
        report_path = tmp_path / "validation_report.json"

        ingest_data(
            output_path=manifest_path,
            run_id="test-run",
            dataset_uri="synthetic://tiny-image-classification",
            n_train=32,
            n_val=16,
            image_size=16,
            n_classes=2,
        )

        report = validate_data(
            manifest_path=manifest_path,
            report_path=report_path,
            run_id="test-run",
        )

        assert report_path.exists()
        assert report["valid"] is True

        loaded = json.loads(report_path.read_text(encoding="utf-8"))
        assert loaded["n_errors"] == 0


    def test_validate_rejects_invalid_manifest(tmp_path) -> None:
        manifest_path = tmp_path / "dataset_manifest.json"
        report_path = tmp_path / "validation_report.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "dataset_uri": "",
                    "run_id": "test-run",
                    "n_train": 0,
                    "n_val": 0,
                    "image_size": 0,
                    "n_classes": 1,
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError):
            validate_data(
                manifest_path=manifest_path,
                report_path=report_path,
                run_id="test-run",
            )

        loaded = json.loads(report_path.read_text(encoding="utf-8"))
        assert loaded["valid"] is False
        assert loaded["n_errors"] > 0
    ```

## Local Test

```bash
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest tests/test_ingest.py tests/test_validate.py
uv run kbd --help
mkdir -p reports/capstone-local
uv run kbd ingest-data-cmd \
  --output-path reports/capstone-local/dataset_manifest.json \
  --run-id capstone-local-cli \
  --dataset-uri synthetic://tiny-image-classification \
  --n-train 32 \
  --n-val 16 \
  --image-size 16 \
  --n-classes 2
uv run kbd validate-data-cmd \
  --manifest-path reports/capstone-local/dataset_manifest.json \
  --report-path reports/capstone-local/validation_report.json \
  --run-id capstone-local-cli
```

## Common Problems

### Component command name differs

Typer converts underscores to hyphens by default in many cases. Verify whether the final commands are:

```text
ingest-data-cmd
validate-data-cmd
```

or:

```text
ingest-data
validate-data
```

Then update component args accordingly.

### Validation report path is a directory

KFP artifact paths can behave like directories depending on artifact type and backend.

If needed, write to:

```text
Path(validation_report.path) / "validation_report.json"
```

and keep the docs aligned.

## Acceptance Criteria

You are done when:

- ingest code exists
- validation code exists
- CLI commands exist
- KFP components exist
- tests pass
- dataset manifest can be uploaded to object storage
- validation report can be uploaded to object storage

## Next Step

Continue with [Final Pipeline](03-final-pipeline.md).
