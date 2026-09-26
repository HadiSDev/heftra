from datetime import datetime

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid


class EmissionFactorSet(SQLModel, table=True):
    """One imported release of spend-based emission factors."""

    __tablename__ = "emission_factor_sets"
    __table_args__ = (UniqueConstraint("source", "version", name="uq_emission_factor_set_version"),)

    id: str = Field(default_factory=_uuid, primary_key=True)
    source: str = Field(sa_type=String, nullable=False)
    version: str = Field(sa_type=String, nullable=False)
    classification: str = Field(sa_type=String, nullable=False)
    currency: str = Field(sa_type=String(3), nullable=False)
    price_year: int = Field(sa_type=Integer, nullable=False)
    price_basis: str = Field(sa_type=String, nullable=False)
    licence: str = Field(sa_type=String, nullable=False)
    attribution: str = Field(sa_type=String, nullable=False)
    active: bool = Field(sa_type=Boolean, nullable=False, default=False)
    imported_at: datetime = Field(sa_column=_ts())
