"""The dashboard's tiles: spend, how much is categorized, suppliers, and what needs attention."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from .period import ReportPeriods


class MonthSpend(BaseModel):
    month: date
    amount: Decimal


class SpendOverviewRow(BaseModel):
    """One base currency's figures."""

    currency: str
    spend: Decimal
    comparison_spend: Decimal
    categorized_spend: Decimal
    unconverted_vouchers: int
    months: list[MonthSpend]
    active_suppliers: int
    new_suppliers: int


class AttentionCounts(BaseModel):
    """Work waiting across the caller's companies, whatever the period."""

    needs_review_lines: int
    failed_documents: int
    totals_mismatch: int


class SpendOverview(ReportPeriods):
    rows: list[SpendOverviewRow]
    attention: AttentionCounts
