"""Shared helpers for model definitions."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, func


def _uuid() -> str:
    return str(uuid4())


def _ts() -> Column:
    return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _changed_ts() -> Column:
    """When what the row says last changed: set on insert, and stamped by change tracking."""
    return Column(DateTime(timezone=True), default=_now, server_default=func.now(),
                  nullable=False)


def _now() -> datetime:
    return datetime.now(timezone.utc)
