"""Failing the jobs a previous process left unfinished."""
from __future__ import annotations

import logging

from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from .jobs import interrupt_unfinished

logger = logging.getLogger(__name__)


def interrupt_stale_jobs(engine: Engine) -> None:
    """Mark queued and running imports as interrupted; a database that isn't ready is logged."""
    try:
        with Session(engine) as session:
            interrupted = interrupt_unfinished(session)
    except SQLAlchemyError as error:
        logger.warning("Could not check for interrupted imports: %s", error)
        return
    if interrupted:
        logger.warning("Marked %d unfinished reference data imports as interrupted", interrupted)
