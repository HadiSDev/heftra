"""An agreement's report, and the dashboard's view of every agreement for a period."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from web_api.db.models import FindingKind, FindingSeverity

from ..common import Page
from ..reports.period import ReportPeriods
from .findings import FindingRead


class FindingTotal(BaseModel):
    kind: FindingKind
    severity: FindingSeverity
    count: int
    amount: Decimal


class CommitmentProgress(BaseModel):
    """How far a volume commitment has got in its current period."""

    term_id: str
    scope: str
    period_start: date
    period_end: date
    committed: Decimal
    spent: Decimal
    target_to_date: Decimal
    forecast: Decimal
    tier_reached: Decimal | None = None
    next_tier: Decimal | None = None


class AgreementReport(BaseModel):
    agreement_id: str
    analysed_at: datetime | None = None
    currency: str | None = None
    in_scope_spend: Decimal = Decimal("0")
    supplier_spend: Decimal = Decimal("0")
    totals: list[FindingTotal] = []
    commitments: list[CommitmentProgress] = []
    findings: Page[FindingRead]


class OffContractSupplier(BaseModel):
    vendor_id: str | None = None
    name: str
    amount: Decimal
    count: int


class AgreementCompliance(ReportPeriods):
    """The period's open rule breaks, for the dashboard."""

    has_active_agreement: bool = False
    currency: str | None = None
    open_rule_breaks: int = 0
    rule_break_amount: Decimal = Decimal("0")
    off_contract_amount: Decimal = Decimal("0")
    overcharge_amount: Decimal = Decimal("0")
    top_suppliers: list[OffContractSupplier] = []
