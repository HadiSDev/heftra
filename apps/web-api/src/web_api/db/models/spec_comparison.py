from datetime import datetime

from sqlalchemy import JSON, Integer, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class SpecComparison(SQLModel, table=True):
    """An LLM's comparison of two specifications, kept so the same pair is never asked twice.

    `kind` is what was compared (product types, tiered parts, other attributes); `result` holds
    each compared attribute's verdict and reason.
    """

    __tablename__ = "spec_comparisons"
    __table_args__ = (
        UniqueConstraint("kind", "left_hash", "right_hash", "version", name="uq_spec_comparison"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    kind: str = Field(sa_type=String, nullable=False)
    left_hash: str = Field(sa_type=String, nullable=False)
    right_hash: str = Field(sa_type=String, nullable=False)
    version: int = Field(sa_type=Integer, nullable=False)
    result: dict = Field(sa_type=JSON, nullable=False)
    created_at: datetime = Field(sa_column=_ts())
