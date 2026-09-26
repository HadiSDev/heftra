"""Spend by category, with the level below, and by supplier, beside the comparison period."""
from __future__ import annotations

from decimal import Decimal

from sqlmodel import Session

from web_api.db.models import Vendor
from web_api.schemas import CategorySpendRead, SpendBreakdown, SpendBreakdownRow, SupplierSpendRead

from .allocation import AllocatedSpend, allocate
from .figures import ZERO, by_currency, by_supplier, report_periods, total, vendor_names, within
from .periods import Period

DEFAULT_SUPPLIERS = 10
MAX_SUPPLIERS = 50


def spend_breakdown(
    session: Session, company_ids: list[str], period: Period, *, limit: int = DEFAULT_SUPPLIERS
) -> SpendBreakdown:
    comparison = period.comparison()
    allocation = allocate(session, company_ids, Period(comparison.start, period.end))
    vendors = vendor_names(session, (row.vendor_id for row in allocation.spend if row.vendor_id))

    rows = []
    for currency, spend in by_currency(allocation.spend).items():
        current, previous = within(spend, period), within(spend, comparison)
        rows.append(SpendBreakdownRow(
            currency=currency,
            spend=total(current),
            categories=_categories(current, previous),
            suppliers=_suppliers(current, previous, vendors, limit),
        ))
    return SpendBreakdown(**report_periods(period).model_dump(), rows=rows)


def _categories(current: list[AllocatedSpend], previous: list[AllocatedSpend]) -> list[CategorySpendRead]:
    """Top-level categories largest first, each with its second level; the uncategorized spend last."""
    now = _sums(current)
    before = _sums(previous)
    names = {key[0] for key in (*now, *before) if key[0] is not None}

    categories = []
    for name in names:
        children_keys = {key for key in (*now, *before) if key[0] == name}
        children = [
            CategorySpendRead(name=child, spend=now.get((name, child), ZERO),
                              comparison_spend=before.get((name, child), ZERO))
            for _, child in children_keys
        ]
        categories.append(CategorySpendRead(
            name=name,
            spend=sum((c.spend for c in children), ZERO),
            comparison_spend=sum((c.comparison_spend for c in children), ZERO),
            children=_largest_first(children),
        ))

    ordered = _largest_first(categories)
    uncategorized = (now.get((None, None), ZERO), before.get((None, None), ZERO))
    if any(uncategorized):
        ordered.append(CategorySpendRead(spend=uncategorized[0], comparison_spend=uncategorized[1]))
    return ordered


def _suppliers(
    current: list[AllocatedSpend],
    previous: list[AllocatedSpend],
    vendors: dict[str, Vendor],
    limit: int,
) -> list[SupplierSpendRead]:
    now = by_supplier(current)
    before = by_supplier(previous)
    ranked = sorted(now, key=lambda vendor_id: (-now[vendor_id], vendors[vendor_id].name))
    return [
        SupplierSpendRead(
            id=vendor_id,
            name=vendors[vendor_id].name,
            country_code=vendors[vendor_id].country_code,
            spend=now[vendor_id],
            comparison_spend=before.get(vendor_id, ZERO),
        )
        for vendor_id in ranked[:limit]
    ]


def _sums(spend: list[AllocatedSpend]) -> dict[tuple[str | None, str | None], Decimal]:
    """Spend per (level 1, level 2), the uncategorized under (None, None)."""
    sums: dict[tuple[str | None, str | None], Decimal] = {}
    for row in spend:
        key = (row.category, row.subcategory) if row.categorized else (None, None)
        sums[key] = sums.get(key, ZERO) + row.amount
    return sums


def _largest_first(categories: list[CategorySpendRead]) -> list[CategorySpendRead]:
    return sorted(
        categories,
        key=lambda c: (-c.spend, -c.comparison_spend, c.name is None, c.name or ""),
    )
