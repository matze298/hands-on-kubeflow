"""Creates a S3 bucket using boto3."""

import boto3
from botocore.client import Config

ENDPOINT_URL = "http://localhost:9000"
BUCKET = "kubeflow-by-doing"

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minioadmin123",  # noqa:S106
    config=Config(signature_version="s3v4"),
)

existing = [b["Name"] for b in s3.list_buckets()["Buckets"]]
if BUCKET not in existing:
    s3.create_bucket(Bucket=BUCKET)

print(f"bucket ready: s3://{BUCKET}")  # noqa:T201
