"""The configured file store."""
from __future__ import annotations

from .. import config
from .errors import StorageUnavailable
from .s3 import S3FileStore, S3Settings
from .store import FileStore


def configured() -> bool:
    return bool(config.S3_ENDPOINT_URL and config.S3_ACCESS_KEY and config.S3_SECRET_KEY)


def file_store() -> FileStore:
    """The S3 store from configuration; raises `StorageUnavailable` when it isn't configured."""
    if not configured():
        raise StorageUnavailable("file storage is not configured (S3_ENDPOINT_URL and keys)")
    return S3FileStore(S3Settings(
        endpoint_url=config.S3_ENDPOINT_URL,
        region=config.S3_REGION,
        bucket=config.S3_BUCKET,
        access_key=config.S3_ACCESS_KEY,
        secret_key=config.S3_SECRET_KEY,
        timeout_seconds=config.S3_TIMEOUT_SECONDS,
    ))
