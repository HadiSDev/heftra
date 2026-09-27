"""A file store held in memory, for tests."""
from __future__ import annotations

from .errors import StoredFileMissing


class MemoryFileStore:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    async def ensure_bucket(self) -> None:
        return None

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = (data, content_type)

    async def get(self, key: str) -> bytes:
        if key not in self.objects:
            raise StoredFileMissing(key)
        return self.objects[key][0]

    async def delete(self, key: str) -> None:
        self.objects.pop(key, None)
