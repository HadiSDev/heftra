"""The memory and S3 file stores, the configured store, and the bucket at startup."""
from __future__ import annotations

import asyncio
import logging

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from web_api import config
from web_api.storage.errors import StorageUnavailable, StoredFileMissing
from web_api.storage.factory import file_store
from web_api.storage.keys import agreement_key
from web_api.storage.memory import MemoryFileStore
from web_api.storage.s3 import S3FileStore, S3Settings
from web_api.storage.startup import ensure_storage

SETTINGS = S3Settings("http://localhost:9100", "us-east-1", "steelyard", "key", "secret", 5)


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code}}, "operation")


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> None:
        return None

    async def read(self) -> bytes:
        return self.data


class FakeS3:
    """What S3FileStore calls on an aioboto3 client, over a dict."""

    def __init__(self, bucket_exists: bool = True, down: bool = False) -> None:
        self.objects: dict[str, bytes] = {}
        self.bucket_exists = bucket_exists
        self.down = down
        self.created: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> None:
        return None

    def _check(self) -> None:
        if self.down:
            raise EndpointConnectionError(endpoint_url="http://localhost:9100")

    async def head_bucket(self, Bucket: str) -> None:
        self._check()
        if not self.bucket_exists:
            raise _client_error("404")

    async def create_bucket(self, Bucket: str) -> None:
        self.created.append(Bucket)
        self.bucket_exists = True

    async def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:
        self._check()
        self.objects[Key] = Body

    async def get_object(self, Bucket: str, Key: str) -> dict:
        self._check()
        if Key not in self.objects:
            raise _client_error("NoSuchKey")
        return {"Body": FakeBody(self.objects[Key])}

    async def delete_object(self, Bucket: str, Key: str) -> None:
        self._check()
        self.objects.pop(Key, None)


def _s3(fake: FakeS3) -> S3FileStore:
    store = S3FileStore(SETTINGS)
    store._client = lambda: fake
    return store


def test_the_memory_store_round_trips():
    store = MemoryFileStore()

    asyncio.run(store.put("a/b.pdf", b"%PDF", "application/pdf"))

    assert asyncio.run(store.get("a/b.pdf")) == b"%PDF"
    asyncio.run(store.delete("a/b.pdf"))
    with pytest.raises(StoredFileMissing):
        asyncio.run(store.get("a/b.pdf"))


def test_the_s3_store_round_trips():
    fake = FakeS3()
    store = _s3(fake)

    asyncio.run(store.put("k.pdf", b"%PDF-1.7", "application/pdf"))

    assert asyncio.run(store.get("k.pdf")) == b"%PDF-1.7"
    asyncio.run(store.delete("k.pdf"))
    assert fake.objects == {}


def test_a_missing_object_is_missing_not_unavailable():
    with pytest.raises(StoredFileMissing):
        asyncio.run(_s3(FakeS3()).get("nothing.pdf"))


def test_an_unreachable_store_is_unavailable():
    with pytest.raises(StorageUnavailable):
        asyncio.run(_s3(FakeS3(down=True)).put("k.pdf", b"x", "application/pdf"))


def test_a_missing_bucket_is_created():
    fake = FakeS3(bucket_exists=False)

    asyncio.run(_s3(fake).ensure_bucket())

    assert fake.created == ["steelyard"]


def test_an_existing_bucket_is_left_alone():
    fake = FakeS3()

    asyncio.run(_s3(fake).ensure_bucket())

    assert fake.created == []


def test_without_settings_there_is_no_store(monkeypatch):
    monkeypatch.setattr(config, "S3_ENDPOINT_URL", "")

    with pytest.raises(StorageUnavailable, match="not configured"):
        file_store()


def test_startup_without_storage_logs_and_carries_on(monkeypatch, caplog):
    monkeypatch.setattr(config, "S3_ENDPOINT_URL", "")
    caplog.set_level(logging.INFO)

    asyncio.run(ensure_storage())

    assert "not configured" in caplog.text


def test_agreement_keys_start_with_the_company():
    key = agreement_key("company-1", "agreement-9")

    assert key.startswith("companies/company-1/agreements/agreement-9/")
    assert key.endswith(".pdf")
