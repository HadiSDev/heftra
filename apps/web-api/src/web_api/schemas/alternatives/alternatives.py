"""An alternative to an item, and a person's review of it."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from web_api.db.models import (
    AlternativeMatch,
    AlternativeReviewStatus,
    AlternativeSource,
    DismissReason,
)


class AttributeComparison(BaseModel):
    """One key attribute of the item beside the alternative's: same, better, worse or
    missing."""

    name: str
    item: str
    candidate: str | None = None
    verdict: str
    reason: str = ""


class AgreementNote(BaseModel):
    """What switching would break under an agreement: `off_contract` or `commitment_behind`."""

    kind: str
    agreement_id: str
    term_id: str
    text: str


class AlternativeRead(BaseModel):
    """`unit_price` is per the item's pricing unit, without VAT, in `currency`. `origin` says
    where it was found: a supplier and company, a number of organizations with a median and
    lowest quartile, or a connector, seller and link."""

    id: str
    item_id: str
    source: AlternativeSource
    match: AlternativeMatch
    name: str
    unit_price: Decimal
    currency: str
    saving_yearly: Decimal | None = None
    saving_percent: Decimal
    comparison: list[AttributeComparison] = []
    origin: dict = {}
    agreement_notes: list[AgreementNote] = []
    review_status: AlternativeReviewStatus
    dismiss_reason: DismissReason | None = None
    review_note: str | None = None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    found_at: datetime


class AlternativeReview(BaseModel):
    review_status: AlternativeReviewStatus
    dismiss_reason: DismissReason | None = None
    note: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _reason_when_dismissed(self) -> AlternativeReview:
        if self.review_status == AlternativeReviewStatus.DISMISSED and self.dismiss_reason is None:
            raise ValueError("A dismissal needs its reason.")
        return self
