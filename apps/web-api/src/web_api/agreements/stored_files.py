"""Removing agreement files from storage after their rows are gone."""
from __future__ import annotations

import logging

from ..storage.blocking import run_blocking
from ..storage.errors import StorageUnavailable
from ..storage.factory import configured, file_store
from ..storage.store import FileStore

logger = logging.getLogger(__name__)


async def discard_files(store: FileStore, keys: list[str]) -> None:
    """Delete each stored file; one that can't be deleted is logged and left behind."""
    for key in keys:
        try:
            await store.delete(key)
        except StorageUnavailable as error:
            logger.warning("Could not delete stored file %s: %s", key, error)


def discard_files_blocking(store: FileStore, keys: list[str]) -> None:
    if keys:
        run_blocking(discard_files(store, keys))


def discard_company_files(keys: list[str]) -> None:
    """Remove a deleted company's files from the configured store, if there is one."""
    if keys and configured():
        discard_files_blocking(file_store(), keys)
