"""The interface every file store offers."""
from __future__ import annotations

from typing import Protocol


class FileStore(Protocol):
    """Puts, gets and deletes whole objects by key."""

    async def ensure_bucket(self) -> None:
        """Create the store's bucket when it doesn't exist."""
        ...

    async def put(self, key: str, data: bytes, content_type: str) -> None:
        ...

    async def get(self, key: str) -> bytes:
        """The object's bytes; raises `StoredFileMissing` when there is none."""
        ...

    async def delete(self, key: str) -> None:
        """Remove the object; a missing one is not an error."""
        ...
