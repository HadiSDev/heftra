"""A file store in an S3-compatible bucket (RustFS locally), through aioboto3."""
from __future__ import annotations

from typing import NamedTuple

import aioboto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from .errors import StorageUnavailable, StoredFileMissing

_MISSING_CODES = {"NoSuchKey", "404", "NotFound"}
_OWNED_CODES = {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}


class S3Settings(NamedTuple):
    endpoint_url: str
    region: str
    bucket: str
    access_key: str
    secret_key: str
    timeout_seconds: float


class S3FileStore:
    def __init__(self, settings: S3Settings) -> None:
        self._settings = settings
        self._session = aioboto3.Session(
            aws_access_key_id=settings.access_key,
            aws_secret_access_key=settings.secret_key,
            region_name=settings.region,
        )
        self._config = Config(
            s3={"addressing_style": "path"},
            connect_timeout=settings.timeout_seconds,
            read_timeout=settings.timeout_seconds,
            retries={"max_attempts": 2},
        )

    def _client(self):
        return self._session.client("s3", endpoint_url=self._settings.endpoint_url,
                                    config=self._config)

    async def ensure_bucket(self) -> None:
        bucket = self._settings.bucket
        try:
            async with self._client() as client:
                try:
                    await client.head_bucket(Bucket=bucket)
                except ClientError as error:
                    if _code(error) not in _MISSING_CODES:
                        raise
                    await _create_bucket(client, bucket)
        except (BotoCoreError, ClientError) as error:
            raise StorageUnavailable(f"bucket {bucket}: {error}") from error

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        try:
            async with self._client() as client:
                await client.put_object(Bucket=self._settings.bucket, Key=key, Body=data,
                                        ContentType=content_type)
        except (BotoCoreError, ClientError) as error:
            raise StorageUnavailable(f"storing {key}: {error}") from error

    async def get(self, key: str) -> bytes:
        try:
            async with self._client() as client:
                response = await client.get_object(Bucket=self._settings.bucket, Key=key)
                async with response["Body"] as body:
                    return await body.read()
        except ClientError as error:
            if _code(error) in _MISSING_CODES:
                raise StoredFileMissing(key) from error
            raise StorageUnavailable(f"reading {key}: {error}") from error
        except BotoCoreError as error:
            raise StorageUnavailable(f"reading {key}: {error}") from error

    async def delete(self, key: str) -> None:
        try:
            async with self._client() as client:
                await client.delete_object(Bucket=self._settings.bucket, Key=key)
        except (BotoCoreError, ClientError) as error:
            raise StorageUnavailable(f"deleting {key}: {error}") from error


async def _create_bucket(client, bucket: str) -> None:
    try:
        await client.create_bucket(Bucket=bucket)
    except ClientError as error:
        if _code(error) not in _OWNED_CODES:
            raise


def _code(error: ClientError) -> str:
    return str(error.response.get("Error", {}).get("Code", ""))
