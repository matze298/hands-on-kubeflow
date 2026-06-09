# Final Pipeline

This page defines the capstone pipeline.

## What You Will Build

You will create:

```text
src/kubeflow_by_doing/registry.py
components/record_or_register_model.py
pipelines/capstone_pipeline.py
```

The final pipeline is:

```text
ingest_data
  ↓
validate_data
  ↓
train_model
  ↓
evaluate_model
  ↓
record_or_register_model
  ↓
deploy_model
  ↓
smoke_test_model
```

## Create `registry.py`

Create `src/kubeflow_by_doing/registry.py` yourself first.

Requirements:

- expose a `record_model(...)` function
- write a JSON model record
- include run ID, model URI, metrics URI, lineage URI, image tag, git SHA, and promotion status
- optionally upload the record under `registry/`
- return the record dictionary

??? example "Reference implementation: `src/kubeflow_by_doing/registry.py`"

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


    def record_model(
        *,
        output_path: Path,
        run_id: str,
        model_uri: str,
        metrics_uri: str,
        lineage_uri: str,
        image_tag: str,
        git_sha: str,
        promoted: bool,
        upload_artifacts: bool = False,
    ) -> dict[str, str | bool]:
        record: dict[str, str | bool] = {
            "run_id": run_id,
            "model_uri": model_uri,
            "metrics_uri": metrics_uri,
            "lineage_uri": lineage_uri,
            "image_tag": image_tag,
            "git_sha": git_sha,
            "promoted": promoted,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        if upload_artifacts:
            config = ObjectStorageConfig.from_env()
            ensure_bucket(config)

            key = f"{run_prefix(run_id)}/registry/model_record.json"
            record_uri = upload_file(local_path=output_path, key=key, config=config)
            record["record_uri"] = record_uri
            output_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        return record
    ```

## Add CLI Command

Update `src/kubeflow_by_doing/cli.py` yourself.

Requirements:

- add a command that calls `record_model(...)`
- expose every model-record field as an option
- include `promoted` and `upload_artifacts` booleans
- print the returned dictionary

??? example "Reference implementation: CLI command"

    ```python
    @app.command()
    def record_model_cmd(
        output_path: Path = typer.Option(...),
        run_id: str = typer.Option(...),
        model_uri: str = typer.Option(...),
        metrics_uri: str = typer.Option(...),
        lineage_uri: str = typer.Option(...),
        image_tag: str = typer.Option(...),
        git_sha: str = typer.Option(...),
        promoted: bool = typer.Option(False),
        upload_artifacts: bool = typer.Option(False),
    ) -> None:
        from kubeflow_by_doing.registry import record_model

        result = record_model(
            output_path=output_path,
            run_id=run_id,
            model_uri=model_uri,
            metrics_uri=metrics_uri,
            lineage_uri=lineage_uri,
            image_tag=image_tag,
            git_sha=git_sha,
            promoted=promoted,
            upload_artifacts=upload_artifacts,
        )
        rprint(result)
    ```

## Create Registry Test

Create `tests/test_registry.py` yourself.

Required coverage:

- record file is written
- returned record says `promoted` when requested
- serialized JSON includes the run ID

??? example "Reference implementation: `tests/test_registry.py`"

    ```python
    from __future__ import annotations

    import json

    from kubeflow_by_doing.registry import record_model


    def test_record_model_writes_record(tmp_path) -> None:
        output_path = tmp_path / "model_record.json"

        record = record_model(
            output_path=output_path,
            run_id="test-run",
            model_uri="s3://bucket/runs/test-run/models/model.pt",
            metrics_uri="s3://bucket/runs/test-run/metrics/metrics.json",
            lineage_uri="s3://bucket/runs/test-run/lineage/lineage.json",
            image_tag="image:tag",
            git_sha="abc1234",
            promoted=True,
        )

        assert output_path.exists()
        assert record["promoted"] is True

        loaded = json.loads(output_path.read_text(encoding="utf-8"))
        assert loaded["run_id"] == "test-run"
    ```

## Create `components/record_or_register_model.py`

Create this component yourself.

Requirements:

- define a `@dsl.container_component`
- write a model-record output artifact
- call the registry CLI command inside the tutorial image
- pass model, metrics, lineage, image, git, and promotion metadata explicitly
- append boolean flags only when enabled

??? example "Reference implementation: `components/record_or_register_model.py`"

    ```python
    from __future__ import annotations

    from kfp import dsl
    from kfp.dsl import Artifact, Output


    @dsl.container_component
    def record_or_register_model(
        model_record: Output[Artifact],
        image: str,
        run_id: str,
        model_uri: str,
        metrics_uri: str,
        lineage_uri: str,
        image_tag: str,
        git_sha: str,
        promoted: bool,
        upload_artifacts: bool = True,
    ) -> dsl.ContainerSpec:
        args = [
            "record-model-cmd",
            "--output-path",
            model_record.path,
            "--run-id",
            run_id,
            "--model-uri",
            model_uri,
            "--metrics-uri",
            metrics_uri,
            "--lineage-uri",
            lineage_uri,
            "--image-tag",
            image_tag,
            "--git-sha",
            git_sha,
        ]

        if promoted:
            args.append("--promoted")

        if upload_artifacts:
            args.append("--upload-artifacts")

        return dsl.ContainerSpec(
            image=image,
            command=["kbd"],
            args=args,
        )
    ```

## Create `pipelines/capstone_pipeline.py`

Create `pipelines/capstone_pipeline.py` yourself first.

Requirements:

- compile to `compiled/capstone_pipeline.yaml`
- expose the parameters from the capstone contract
- use the artifact bucket parameter when constructing durable artifact URIs
- run `ingest_data` before `validate_data`
- run training only after validation
- run evaluation only after training
- choose CPU or GPU image from the `accelerator` parameter
- attach object-storage credentials to tasks that read or write artifacts
- evaluate before promotion
- write lineage and registry state only after promotion
- make deployment conditional through `deploy_after_promotion`
- keep the first runnable path CPU-safe

Hints:

- keep helper functions for shared secret injection and training resource setup
- reuse the component modules introduced in earlier chapters
- compile early and often; KFP SDK errors are easier to fix before running the pipeline

??? example "Reference implementation: `pipelines/capstone_pipeline.py`"

    ```python
    from __future__ import annotations

    from kfp import compiler, dsl
    from kfp import kubernetes

    from components.deploy_model import deploy_model
    from components.evaluate_model import evaluate_model
    from components.ingest_data import ingest_data
    from components.promote_model import promote_model, read_accuracy
    from components.record_or_register_model import record_or_register_model
    from components.smoke_test_model import smoke_test_model
    from components.train_model import train_model
    from components.validate_data import validate_data
    from components.write_lineage import write_lineage


    SECRET_ENV = {
        "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY": "AWS_SECRET_ACCESS_KEY",
        "AWS_DEFAULT_REGION": "AWS_DEFAULT_REGION",
        "KBD_S3_ENDPOINT_URL": "KBD_S3_ENDPOINT_URL",
        "KBD_ARTIFACT_BUCKET": "KBD_ARTIFACT_BUCKET",
        "MLFLOW_S3_ENDPOINT_URL": "MLFLOW_S3_ENDPOINT_URL",
        "MLFLOW_TRACKING_URI": "MLFLOW_TRACKING_URI",
        "MLFLOW_EXPERIMENT_NAME": "MLFLOW_EXPERIMENT_NAME",
    }


    def attach_artifact_secret(task: dsl.PipelineTask) -> dsl.PipelineTask:
        kubernetes.use_secret_as_env(
            task,
            secret_name="artifact-store-credentials",
            secret_key_to_env=SECRET_ENV,
        )
        return task


    def configure_training_resources(
        task: dsl.PipelineTask,
        accelerator: str,
        gpu_count: int,
    ) -> dsl.PipelineTask:
        if accelerator == "gpu":
            task.set_accelerator_type("nvidia.com/gpu")
            task.set_accelerator_limit(gpu_count)
            task.set_cpu_request("2")
            task.set_memory_request("4Gi")
            task.set_memory_limit("8Gi")
        else:
            task.set_cpu_request("1")
            task.set_memory_request("2Gi")
            task.set_memory_limit("4Gi")

        return task


    @dsl.pipeline(name="kubeflow-by-doing-capstone")
    def capstone_pipeline(
        run_id: str = "capstone-local-001",
        dataset_uri: str = "synthetic://tiny-image-classification",
        accelerator: str = "cpu",
        gpu_count: int = 0,
        cpu_image: str = "kubeflow-by-doing/train:local",
        gpu_image: str = "kubeflow-by-doing/train:gpu-local",
        serve_image: str = "kubeflow-by-doing/serve:local",
        artifact_bucket: str = "kubeflow-by-doing",
        min_accuracy: float = 0.5,
        deploy_after_promotion: bool = False,
        git_sha: str = "unknown",
        n_train: int = 256,
        n_val: int = 64,
        image_size: int = 16,
        n_classes: int = 2,
        epochs: int = 2,
        learning_rate: float = 1e-3,
        batch_size: int = 32,
    ) -> None:
        training_image = gpu_image if accelerator == "gpu" else cpu_image
        training_device = "cuda" if accelerator == "gpu" else "cpu"

        artifact_prefix = f"s3://{artifact_bucket}/runs/{run_id}"
        model_uri = f"{artifact_prefix}/models/model.pt"
        metrics_uri = f"{artifact_prefix}/metrics/metrics.json"
        lineage_uri = f"{artifact_prefix}/lineage/lineage.json"
        image_tag = training_image

        ingest_task = ingest_data(
            image=cpu_image,
            run_id=run_id,
            dataset_uri=dataset_uri,
            n_train=n_train,
            n_val=n_val,
            image_size=image_size,
            n_classes=n_classes,
            upload_artifacts=True,
        )
        attach_artifact_secret(ingest_task)

        validate_task = validate_data(
            dataset_manifest=ingest_task.outputs["dataset_manifest"],
            image=cpu_image,
            run_id=run_id,
            upload_artifacts=True,
        )
        attach_artifact_secret(validate_task)

        train_task = train_model(
            image=training_image,
            device=training_device,
            epochs=epochs,
            learning_rate=learning_rate,
            seed=42,
            n_train=n_train,
            n_val=n_val,
            batch_size=batch_size,
            run_id=run_id,
            upload_artifacts=True,
            tracking=True,
            image_tag=image_tag,
            git_sha=git_sha,
        ).after(validate_task)
        attach_artifact_secret(train_task)
        configure_training_resources(train_task, accelerator=accelerator, gpu_count=gpu_count)

        evaluate_task = evaluate_model(
            model=train_task.outputs["model"],
            seed=42,
            device="cpu",
            n_train=n_train,
            n_val=n_val,
            batch_size=batch_size,
        ).after(train_task)
        attach_artifact_secret(evaluate_task)

        accuracy_task = read_accuracy(
            metrics_path=evaluate_task.outputs["metrics_artifact"],
        )

        with dsl.If(accuracy_task.output >= min_accuracy):
            promote_task = promote_model(
                model=train_task.outputs["model"],
                accuracy=accuracy_task.output,
                min_accuracy=min_accuracy,
            )

            lineage_task = write_lineage(
                run_id=run_id,
                git_sha=git_sha,
                image_tag=image_tag,
                dataset_uri=dataset_uri,
                model_uri=model_uri,
                metrics_uri=metrics_uri,
                artifact_prefix=artifact_prefix,
                kfp_run_id=run_id,
            ).after(promote_task)
            attach_artifact_secret(lineage_task)

            record_task = record_or_register_model(
                image=cpu_image,
                run_id=run_id,
                model_uri=model_uri,
                metrics_uri=metrics_uri,
                lineage_uri=lineage_uri,
                image_tag=image_tag,
                git_sha=git_sha,
                promoted=True,
                upload_artifacts=True,
            ).after(lineage_task)
            attach_artifact_secret(record_task)

            with dsl.If(deploy_after_promotion == True):  # noqa: E712
                deploy_task = deploy_model(
                    model_uri=model_uri,
                    serve_image=serve_image,
                ).after(record_task)
                kubernetes.set_service_account_name(deploy_task, "pipeline-deployer")
                smoke_test_model().after(deploy_task)


    if __name__ == "__main__":
        compiler.Compiler().compile(
            pipeline_func=capstone_pipeline,
            package_path="compiled/capstone_pipeline.yaml",
        )
    ```

!!! warning

    Verify this file against the installed KFP SDK. In particular, check `kubernetes.use_secret_as_env`, `set_service_account_name`, accelerator methods, and conditional syntax.

## Compile

```bash
uv run python pipelines/capstone_pipeline.py
```

Verify:

```bash
ls -lh compiled/capstone_pipeline.yaml
```

## Local Checks

```bash
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest
```

## Acceptance Criteria

You are done when:

- registry helper exists
- registry test passes
- `record_or_register_model` component exists
- capstone pipeline exists
- capstone pipeline compiles
- KFP SDK compatibility issues are resolved
- CPU and GPU image parameters are explicit

## Next Step

Continue with [Run the Capstone](04-run-the-capstone.md).
