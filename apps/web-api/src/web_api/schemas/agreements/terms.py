"""An agreement's terms: as read, as a person adds one, and as a person edits one."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from web_api.db.models import AgreementTermKind, AgreementTermSource, AgreementTermStatus


class TermQuote(BaseModel):
    text: str
    page: int | None = None


class RebateTier(BaseModel):
    threshold: Decimal = Field(ge=0)
    rebate_percent: Decimal = Field(ge=0, le=100)


class TermFields(BaseModel):
    """What every kind of term can say; each kind uses its own fields."""

    scope: str = Field(min_length=1)
    conditions: str | None = None
    item: str | None = None
    unit: str | None = None
    unit_price: Decimal | None = Field(default=None, ge=0)
    discount_percent: Decimal | None = Field(default=None, gt=0, le=100)
    commitment_amount: Decimal | None = Field(default=None, gt=0)
    commitment_period: str | None = None
    tiers: list[RebateTier] | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    scope_category_ids: list[str] = []


class TermCreate(TermFields):
    kind: AgreementTermKind


class TermPatch(BaseModel):
    """Only the fields sent are changed."""

    status: AgreementTermStatus | None = None
    scope: str | None = Field(default=None, min_length=1)
    conditions: str | None = None
    item: str | None = None
    unit: str | None = None
    unit_price: Decimal | None = Field(default=None, ge=0)
    discount_percent: Decimal | None = Field(default=None, gt=0, le=100)
    commitment_amount: Decimal | None = Field(default=None, gt=0)
    commitment_period: str | None = None
    tiers: list[RebateTier] | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    scope_category_ids: list[str] | None = None


class TermRead(TermFields):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agreement_id: str
    kind: AgreementTermKind
    status: AgreementTermStatus
    source: AgreementTermSource
    quotes: list[TermQuote] = []
    confidence: Decimal | None = None
    created_at: datetime
    updated_at: datetime | None = None
