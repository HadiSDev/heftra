"""Changes in the spend worth a look."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from .period import ReportPeriods


class SupplierInsight(BaseModel):
    """A supplier and the amount the insight is about: its spend, its rise, or its monthly average."""

    id: str
    name: str
    amount: Decimal
    comparison_amount: Decimal | None = None
    active_months: int | None = None


class UncategorizedInsight(BaseModel):
    """A voucher whose spend is not categorized, addressed as Spend Lines opens it."""

    voucher_id: str | None = None
    entry_id: str | None = None
    invoice_id: str | None = None
    supplier_id: str | None = None
    supplier_name: str | None = None
    spent_on: date
    amount: Decimal


class SpendInsightsRow(BaseModel):
    currency: str
    new_suppliers: list[SupplierInsight]
    increases: list[SupplierInsight]
    recurring: list[SupplierInsight]
    uncategorized: list[UncategorizedInsight]


class SpendInsights(ReportPeriods):
    rows: list[SpendInsightsRow]
