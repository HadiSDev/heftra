from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, DateTime, Numeric, String
from sqlmodel import Field, SQLModel

from ._base import _ts, _uuid
from .agreement_enums import AgreementTermSource, AgreementTermStatus


class AgreementTerm(SQLModel, table=True):
    """One obligation or price in an agreement, with the clause it came from.

    `quotes` holds `[{"text", "page"}]`; `tiers` holds `[{"threshold", "rebate_percent"}]`.
    """

    __tablename__ = "agreement_terms"

    id: str = Field(default_factory=_uuid, primary_key=True)
    agreement_id: str = Field(sa_type=String, foreign_key="agreements.id", nullable=False,
                              index=True)
    kind: str = Field(sa_type=String, nullable=False)
    status: str = Field(sa_type=String, nullable=False,
                        default=AgreementTermStatus.DRAFT.value)
    source: str = Field(sa_type=String, nullable=False, default=AgreementTermSource.AI.value)
    scope: str = Field(sa_type=String, nullable=False)
    conditions: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    item: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    unit: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    unit_price: Optional[Decimal] = Field(sa_type=Numeric(14, 4), nullable=True, default=None)
    discount_percent: Optional[Decimal] = Field(sa_type=Numeric(6, 3), nullable=True,
                                                default=None)
    commitment_amount: Optional[Decimal] = Field(sa_type=Numeric(14, 2), nullable=True,
                                                 default=None)
    commitment_period: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    tiers: Optional[list] = Field(sa_type=JSON, nullable=True, default=None)
    currency: Optional[str] = Field(sa_type=String(3), nullable=True, default=None)
    scope_category_ids: list = Field(sa_type=JSON, nullable=False, default_factory=list)
    quotes: list = Field(sa_type=JSON, nullable=False, default_factory=list)
    confidence: Optional[Decimal] = Field(sa_type=Numeric(4, 3), nullable=True, default=None)
    created_at: datetime = Field(sa_column=_ts())
    updated_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True,
                                           default=None)
