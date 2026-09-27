"""What analysis found against a term, and a person's review of it."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from web_api.db.models import (
    AgreementTermKind,
    FindingKind,
    FindingReviewStatus,
    FindingSeverity,
)


class FindingRead(BaseModel):
    id: str
    agreement_id: str
    term_id: str
    term_kind: AgreementTermKind
    term_scope: str
    term_conditions: str | None = None
    kind: FindingKind
    severity: FindingSeverity
    amount: Decimal
    line_amount: Decimal
    currency: str | None = None
    expected: Decimal | None = None
    actual: Decimal | None = None
    quantity: Decimal | None = None
    reason: str
    judge_confidence: Decimal | None = None
    spent_on: date | None = None
    invoice_line_id: str
    invoice_id: str
    voucher_id: str | None = None
    item: str | None = None
    supplier_name: str | None = None
    from_supplier: bool
    review_status: FindingReviewStatus
    review_note: str | None = None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None


class FindingReview(BaseModel):
    review_status: FindingReviewStatus
    note: str | None = Field(default=None, max_length=1000)
