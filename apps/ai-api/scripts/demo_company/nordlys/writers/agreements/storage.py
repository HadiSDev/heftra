"""Putting the agreement PDFs in the app's file store, when one is reachable."""
from __future__ import annotations

from web_api.agreements.constants import PDF_MEDIA_TYPE
from web_api.agreements.stored_files import discard_company_files
from web_api.storage.blocking import run_blocking
from web_api.storage.errors import StorageUnavailable
from web_api.storage.factory import file_store


async def _put_all(files: dict[str, bytes]) -> None:
    store = file_store()
    await store.ensure_bucket()
    for key, data in files.items():
        await store.put(key, data, PDF_MEDIA_TYPE)


def upload_pdfs(files: dict[str, bytes]) -> str | None:
    """Store each PDF under its key; returns why they couldn't be stored, or None."""
    try:
        run_blocking(_put_all(files))
    except StorageUnavailable as error:
        return str(error)
    return None


def discard_pdfs(keys: list[str]) -> None:
    """Remove stored PDFs of a removed company, if storage is configured."""
    try:
        discard_company_files(keys)
    except StorageUnavailable:
        return
