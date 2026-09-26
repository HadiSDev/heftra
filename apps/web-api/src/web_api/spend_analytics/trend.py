"""Monthly spend over twelve months, stacked by the top categories."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from web_api.schemas import SpendTrend, SpendTrendRow, TrendSeries

from .allocation import AllocatedSpend, allocate
from .figures import ZERO, by_currency, report_periods, total
from .periods import Period, month_start, months_span, trailing_months

TOP_CATEGORIES = 5


def spend_trend(session: Session, company_ids: list[str], period: Period) -> SpendTrend:
    months = trailing_months(period.end)
    allocation = allocate(session, company_ids, months_span(period.end))
    rows = [
        SpendTrendRow(currency=currency, months=months, series=_series(spend, months))
        for currency, spend in by_currency(allocation.spend).items()
    ]
    return SpendTrend(**report_periods(period).model_dump(), rows=rows)


def top_categories(spend: list[AllocatedSpend], count: int = TOP_CATEGORIES) -> list[str]:
    """The top-level categories with the most spend, largest first, ties by name."""
    totals: dict[str, Decimal] = {}
    for row in spend:
        if row.categorized and row.category:
            totals[row.category] = totals.get(row.category, ZERO) + row.amount
    return sorted(totals, key=lambda name: (-totals[name], name))[:count]


def _series(spend: list[AllocatedSpend], months: list[date]) -> list[TrendSeries]:
    top = top_categories(spend)
    named = [
        TrendSeries(kind="category", name=name,
                    amounts=_monthly([row for row in spend if row.categorized and row.category == name], months))
        for name in top
    ]
    others = [row for row in spend if row.categorized and row.category not in top]
    uncategorized = [row for row in spend if not row.categorized]
    if others:
        named.append(TrendSeries(kind="other", amounts=_monthly(others, months)))
    if uncategorized:
        named.append(TrendSeries(kind="not_categorized", amounts=_monthly(uncategorized, months)))
    return named


def _monthly(spend: list[AllocatedSpend], months: list[date]) -> list[Decimal]:
    return [total(row for row in spend if month_start(row.spent_on) == month) for month in months]
