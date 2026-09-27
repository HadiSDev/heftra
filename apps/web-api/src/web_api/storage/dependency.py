"""The file store as a request dependency, so tests can swap it."""
from __future__ import annotations

from fastapi import HTTPException, status

from .errors import StorageUnavailable
from .factory import file_store
from .store import FileStore


def get_file_store() -> FileStore:
    try:
        return file_store()
    except StorageUnavailable as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="File storage is unavailable") from error
