from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, DateTime, Numeric, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _uuid
from .alternative_enums import AlternativeReviewStatus


class ItemAlternative(SQLModel, table=True):
    """Something cheaper than an item, where it was found, and how a person reviewed it.

    `unit_price` is per the item's pricing unit, without VAT, in the company's base currency.
    `ref_key` names what the alternative is (another item, a benchmark, an offer) so a new search
    updates it and a dismissal holds. `comparison` lists the attributes side by side; `origin`
    holds what the source says of it; `agreement_notes` what switching would break.
    """

    __tablename__ = "item_alternatives"
    __table_args__ = (
        UniqueConstraint("item_id", "source", "ref_key", name="uq_item_alternative"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    company_id: str = Field(sa_type=String, foreign_key="companies.id", nullable=False, index=True)
    item_id: str = Field(sa_type=String, foreign_key="company_items.id", nullable=False,
                         index=True)
    source: str = Field(sa_type=String, nullable=False)
    match: str = Field(sa_type=String, nullable=False)
    ref_key: str = Field(sa_type=String, nullable=False)
    name: str = Field(sa_type=String, nullable=False)
    unit_price: Decimal = Field(sa_type=Numeric(18, 6), nullable=False)
    currency: str = Field(sa_type=String(3), nullable=False)
    saving_yearly: Optional[Decimal] = Field(sa_type=Numeric(16, 2), nullable=True, default=None)
    saving_percent: Decimal = Field(sa_type=Numeric(7, 2), nullable=False)
    comparison: list = Field(sa_type=JSON, nullable=False, default_factory=list)
    origin: dict = Field(sa_type=JSON, nullable=False, default_factory=dict)
    agreement_notes: list = Field(sa_type=JSON, nullable=False, default_factory=list)
    review_status: str = Field(sa_type=String, nullable=False,
                               default=AlternativeReviewStatus.OPEN.value)
    dismiss_reason: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    review_note: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    reviewed_by: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    reviewed_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True,
                                            default=None)
    found_at: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)
