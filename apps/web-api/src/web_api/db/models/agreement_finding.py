from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Numeric, String, UniqueConstraint
from sqlmodel import Field, SQLModel

from ._base import _uuid
from .agreement_enums import FindingReviewStatus


class AgreementFinding(SQLModel, table=True):
    """What analysis found for one line against one term, and how a person reviewed it.

    `amount` is what the finding is worth and `line_amount` the line's whole net spend, both in
    the company's base currency; `expected` and `actual` are unit prices or percentages in the
    agreement's currency.
    """

    __tablename__ = "agreement_findings"
    __table_args__ = (
        UniqueConstraint("term_id", "invoice_line_id", "kind", name="uq_agreement_finding"),
    )

    id: str = Field(default_factory=_uuid, primary_key=True)
    company_id: str = Field(sa_type=String, foreign_key="companies.id", nullable=False, index=True)
    agreement_id: str = Field(sa_type=String, foreign_key="agreements.id", nullable=False,
                              index=True)
    term_id: str = Field(sa_type=String, foreign_key="agreement_terms.id", nullable=False)
    invoice_line_id: str = Field(sa_type=String, foreign_key="invoice_lines.id", nullable=False)
    invoice_id: str = Field(sa_type=String, foreign_key="invoices.id", nullable=False)
    vendor_id: Optional[str] = Field(sa_type=String, foreign_key="vendors.id", nullable=True,
                                     default=None)
    kind: str = Field(sa_type=String, nullable=False)
    severity: str = Field(sa_type=String, nullable=False)
    amount: Decimal = Field(sa_type=Numeric(14, 2), nullable=False)
    line_amount: Decimal = Field(sa_type=Numeric(14, 2), nullable=False)
    from_supplier: bool = Field(sa_type=Boolean, nullable=False)
    currency: Optional[str] = Field(sa_type=String(3), nullable=True, default=None)
    expected: Optional[Decimal] = Field(sa_type=Numeric(14, 4), nullable=True, default=None)
    actual: Optional[Decimal] = Field(sa_type=Numeric(14, 4), nullable=True, default=None)
    quantity: Optional[Decimal] = Field(sa_type=Numeric(12, 4), nullable=True, default=None)
    reason: str = Field(sa_type=String, nullable=False)
    judge_confidence: Optional[Decimal] = Field(sa_type=Numeric(4, 3), nullable=True,
                                                default=None)
    spent_on: Optional[date] = Field(sa_type=Date, nullable=True, default=None)
    computed_at: datetime = Field(sa_type=DateTime(timezone=True), nullable=False)
    review_status: str = Field(sa_type=String, nullable=False,
                               default=FindingReviewStatus.OPEN.value)
    review_note: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    reviewed_by: Optional[str] = Field(sa_type=String, nullable=True, default=None)
    reviewed_at: Optional[datetime] = Field(sa_type=DateTime(timezone=True), nullable=True,
                                            default=None)
