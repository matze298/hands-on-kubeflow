"""Script uploading a small artifact to test the S3 storage & it's corresponding code."""

from pathlib import Path

from kubeflow_by_doing.storage import ObjectStorageConfig, ensure_bucket, upload_file

config = ObjectStorageConfig.from_env()
ensure_bucket(config)

uri = upload_file(
    local_path=Path("outputs/artifact-test/hello.txt"),
    key="reports/hello.txt",
    config=config,
)

print(uri)  # noqa:T201
