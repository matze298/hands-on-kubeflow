"""Lists the content inside of an S3 bucket."""

from kubeflow_by_doing.storage import ObjectStorageConfig, s3_client

config = ObjectStorageConfig.from_env()
client = s3_client(config)

response = client.list_objects_v2(
    Bucket=config.bucket,
    Prefix="runs/manual-local-001/",
)

for item in response.get("Contents", []):
    print(f"s3://{config.bucket}/{item['Key']}")  # noqa:T201
