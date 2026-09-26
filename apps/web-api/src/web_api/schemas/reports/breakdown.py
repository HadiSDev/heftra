"""Spend by category and by supplier, beside the comparison period's."""
from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from .period import ReportPeriods


class CategorySpendRead(BaseModel):
    """A category's spend in both periods; `name` is None for the uncategorized spend."""

    name: str | None = None
    spend: Decimal
    comparison_spend: Decimal
    children: list[CategorySpendRead] = []


class SupplierSpendRead(BaseModel):
    id: str
    name: str
    country_code: str | None = None
    spend: Decimal
    comparison_spend: Decimal


class SpendBreakdownRow(BaseModel):
    currency: str
    spend: Decimal
    categories: list[CategorySpendRead]
    suppliers: list[SupplierSpendRead]


class SpendBreakdown(ReportPeriods):
    rows: list[SpendBreakdownRow]
