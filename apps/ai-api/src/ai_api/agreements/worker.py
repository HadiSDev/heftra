"""The worker's turn at pending agreements."""
from __future__ import annotations

import logging

from sqlalchemy.engine import Engine

from web_api.storage.factory import configured, file_store

from ..config import get_llm
from .runner import read_pending

logger = logging.getLogger("ai_api.agreements")

AGREEMENT_BATCH = 2


def read_pending_agreements(engine: Engine) -> bool:
    """Read a few pending agreements. Returns whether there were any."""
    if not configured():
        return False
    llm = get_llm()
    counts = read_pending(engine, file_store(), llm.call, limit=AGREEMENT_BATCH)
    if counts["read"] or counts["failed"]:
        logger.info("agreements: %d read, %d failed", counts["read"], counts["failed"])
        return True
    return False
