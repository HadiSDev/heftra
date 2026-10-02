"""Agreements as listed, as shown, and as a person corrects their header."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from web_api.db.models import AgreementStatus, PipelineRunStatus

from .terms import TermRead


class AgreementSupplier(BaseModel):
    vendor_id: str
    name: str


class AgreementFileRead(BaseModel):
    filename: str
    file_size: int | None = None


class AgreementSummaryRead(BaseModel):
    """An agreement in the list, with what its analysis has found."""

    id: str
    company_id: str
    title: str
    reference: str | None = None
    supplier: AgreementSupplier | None = None
    supplier_name: str | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    currency: str | None = None
    status: AgreementStatus
    expired: bool = False
    read_error: str | None = None
    analysed_at: datetime | None = None
    created_at: datetime
    open_rule_breaks: int = 0
    rule_break_amount: Decimal = Decimal("0")
    base_currency: str | None = None


class AgreementAnalysisRead(BaseModel):
    """The company's latest check of its spend against its agreements."""

    id: str
    status: PipelineRunStatus
    requested_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    capped_terms: int = 0
    similarity_available: bool = True
    unjudged_items: int = 0


class AgreementRead(AgreementSummaryRead):
    """An agreement with everything its page shows."""

    supplier_vat_number: str | None = None
    supplier_website: str | None = None
    summary: str | None = None
    read_at: datetime | None = None
    file: AgreementFileRead
    terms: list[TermRead] = []
    analysis: AgreementAnalysisRead | None = None


class AgreementPatch(BaseModel):
    """Only the fields sent are changed; `vendor_id` null unlinks the supplier."""

    vendor_id: str | None = None
    title: str | None = Field(default=None, min_length=1)
    reference: str | None = None
    starts_on: date | None = None
    ends_on: date | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
