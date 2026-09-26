"""Emission sectors already chosen for a question, so it is not asked twice."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, UniqueConstraint
from sqlmodel import Field, SQLModel

from web_api.db.models._base import _ts, _uuid


class EmissionSectorCache(SQLModel, table=True):
    """One remembered answer: a sector, or none when nothing fitted."""

    __tablename__ = "emission_sector_cache"
    __table_args__ = (
        UniqueConstraint(
            "question_key", "classification", name="uq_emission_sector_cache_question"
        ),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    question_key: str = Field(sa_type=String, nullable=False, index=True)
    classification: str = Field(sa_type=String, nullable=False)
    sector_id: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    confidence: Optional[float] = Field(default=None)
    rationale: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    question_sample: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    created_at: datetime = Field(sa_column=_ts())
