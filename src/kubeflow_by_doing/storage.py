"""Helpers for writing tutorial artifacts to S3-compatible object storage."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import boto3
from botocore.client import BaseClient, Config

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ObjectStorageConfig:
    """Configuration for S3-compatible object storage."""

    endpoint_url: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    region_name: str = "us-east-1"

    @classmethod
    def from_env(cls) -> ObjectStorageConfig:
        """Load object-storage settings from the tutorial environment variables.

        Returns:
            Object storage configuration built from `KBD_S3_ENDPOINT_URL`,
            `KBD_ARTIFACT_BUCKET`, `AWS_ACCESS_KEY_ID`,
            `AWS_SECRET_ACCESS_KEY`, and optional `AWS_DEFAULT_REGION`.
        """
        return cls(
            endpoint_url=os.environ["KBD_S3_ENDPOINT_URL"],
            bucket=os.environ["KBD_ARTIFACT_BUCKET"],
            access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        )


def s3_client(config: ObjectStorageConfig) -> BaseClient:
    """Create a boto3 S3 client for AWS or S3-compatible object storage.

    Args:
        config: Endpoint, bucket, credential, and region settings.

    Returns:
        Configured boto3 S3 client using signature version 4.
    """
    return boto3.client(
        "s3",
        endpoint_url=config.endpoint_url,
        aws_access_key_id=config.access_key_id,
        aws_secret_access_key=config.secret_access_key,
        region_name=config.region_name,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket(config: ObjectStorageConfig) -> None:
    """Create the configured bucket when it does not already exist.

    Args:
        config: Object-storage settings containing the target bucket.
    """
    client = s3_client(config)
    existing = [bucket["Name"] for bucket in client.list_buckets()["Buckets"]]
    if config.bucket not in existing:
        client.create_bucket(Bucket=config.bucket)


def upload_file(
    *,
    local_path: Path,
    key: str,
    config: ObjectStorageConfig,
) -> str:
    """Upload one local file to the configured object-storage bucket.

    Args:
        local_path: Path to the local file to upload.
        key: Object key to write inside the configured bucket.
        config: Object-storage settings and credentials.

    Returns:
        `s3://` URI for the uploaded object.
    """
    client = s3_client(config)
    client.upload_file(str(local_path), config.bucket, key)
    return f"s3://{config.bucket}/{key}"


def upload_directory(
    *,
    local_dir: Path,
    prefix: str,
    config: ObjectStorageConfig,
) -> list[str]:
    """Upload every file below a local directory under an object prefix.

    Args:
        local_dir: Directory to walk recursively.
        prefix: Object key prefix to prepend to each relative file path.
        config: Object-storage settings and credentials.

    Returns:
        `s3://` URIs for all uploaded files.
    """
    uris: list[str] = []
    for path in local_dir.rglob("*"):
        if path.is_file():
            relative = path.relative_to(local_dir).as_posix()
            key = f"{prefix.rstrip('/')}/{relative}"
            uris.append(upload_file(local_path=path, key=key, config=config))
    return uris


def run_prefix(run_id: str) -> str:
    """Return the object key prefix used for one pipeline or training run.

    Args:
        run_id: Stable identifier for the run.

    Returns:
        Object key prefix below `runs/`.
    """
    return f"runs/{run_id}"
