"""Monthly spend by the top categories."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from .period import ReportPeriods

SeriesKind = Literal["category", "other", "not_categorized"]


class TrendSeries(BaseModel):
    """One stack of the chart: a category, the rest together, or the uncategorized spend."""

    kind: SeriesKind
    name: str | None = None
    amounts: list[Decimal]


class SpendTrendRow(BaseModel):
    currency: str
    months: list[date]
    series: list[TrendSeries]


class SpendTrend(ReportPeriods):
    rows: list[SpendTrendRow]
