"""Making sure the bucket exists when the web API starts."""
from __future__ import annotations

import logging

from .errors import StorageUnavailable
from .factory import configured, file_store

logger = logging.getLogger(__name__)


async def ensure_storage() -> None:
    """Create the bucket if needed; storage that is missing or down is logged, not fatal."""
    if not configured():
        logger.info("File storage is not configured; uploads will be refused")
        return
    try:
        await file_store().ensure_bucket()
    except StorageUnavailable as error:
        logger.warning("File storage is unavailable: %s", error)
