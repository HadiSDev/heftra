"""Changes worth a look: new suppliers, the biggest rises, recurring spend, uncategorized spend."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from web_api.db.models import Vendor
from web_api.schemas import SpendInsights, SpendInsightsRow, SupplierInsight, UncategorizedInsight

from .allocation import AllocatedSpend, allocate
from .figures import ZERO, by_currency, by_supplier, first_invoice_dates, report_periods, vendor_names, within
from .periods import Period, month_start, trailing_months

LIST_SIZE = 5
RECURRING_MONTHS = 6
RECURRING_AT_LEAST = 3
_CENT = Decimal("0.01")


def spend_insights(session: Session, company_ids: list[str], period: Period) -> SpendInsights:
    comparison = period.comparison()
    months = trailing_months(period.end, RECURRING_MONTHS)
    allocation = allocate(session, company_ids, Period(min(comparison.start, months[0]), period.end))
    vendors = vendor_names(session, (row.vendor_id for row in allocation.spend if row.vendor_id))
    first_invoices = first_invoice_dates(session, company_ids)
    new_ids = {vendor_id for vendor_id, first in first_invoices.items() if period.contains(first)}

    rows = []
    for currency, spend in by_currency(allocation.spend).items():
        now = by_supplier(within(spend, period))
        before = by_supplier(within(spend, comparison))
        rows.append(SpendInsightsRow(
            currency=currency,
            new_suppliers=_new_suppliers(now, new_ids, vendors),
            increases=_increases(now, before, new_ids, vendors),
            recurring=_recurring(spend, months, vendors),
            uncategorized=_uncategorized(within(spend, period), vendors),
        ))
    return SpendInsights(**report_periods(period).model_dump(), rows=rows)


def _new_suppliers(now: dict[str, Decimal], new_ids: set[str], vendors: dict[str, Vendor]) -> list[SupplierInsight]:
    fresh = [vendor_id for vendor_id in now if vendor_id in new_ids]
    ranked = sorted(fresh, key=lambda vendor_id: (-now[vendor_id], vendors[vendor_id].name))
    return [_insight(vendor_id, vendors, now[vendor_id]) for vendor_id in ranked[:LIST_SIZE]]


def _increases(
    now: dict[str, Decimal], before: dict[str, Decimal], new_ids: set[str], vendors: dict[str, Vendor]
) -> list[SupplierInsight]:
    """Suppliers whose spend rose most, leaving out the new ones listed already."""
    rises = {
        vendor_id: amount - before.get(vendor_id, ZERO)
        for vendor_id, amount in now.items()
        if vendor_id not in new_ids and amount > before.get(vendor_id, ZERO)
    }
    ranked = sorted(rises, key=lambda vendor_id: (-rises[vendor_id], vendors[vendor_id].name))
    return [
        _insight(vendor_id, vendors, now[vendor_id], comparison_amount=before.get(vendor_id, ZERO))
        for vendor_id in ranked[:LIST_SIZE]
    ]


def _recurring(
    spend: list[AllocatedSpend], months: list[date], vendors: dict[str, Vendor]
) -> list[SupplierInsight]:
    """Suppliers with spend in at least three of the six months, by their average over those months."""
    averages: dict[str, tuple[Decimal, int]] = {}
    for vendor_id, per_month in _monthly_by_supplier(spend, months).items():
        active = [amount for amount in per_month.values() if amount > 0]
        if len(active) >= RECURRING_AT_LEAST:
            averages[vendor_id] = (sum(active, ZERO) / len(active), len(active))
    ranked = sorted(averages, key=lambda vendor_id: (-averages[vendor_id][0], vendors[vendor_id].name))
    return [
        _insight(vendor_id, vendors, averages[vendor_id][0].quantize(_CENT),
                 active_months=averages[vendor_id][1])
        for vendor_id in ranked[:LIST_SIZE]
    ]


def _monthly_by_supplier(
    spend: list[AllocatedSpend], months: list[date]
) -> dict[str, dict[date, Decimal]]:
    """`{vendor_id: {month: spend}}` over the given months."""
    monthly: dict[str, dict[date, Decimal]] = {}
    for row in spend:
        month = month_start(row.spent_on)
        if row.vendor_id and month in months:
            per_month = monthly.setdefault(row.vendor_id, {})
            per_month[month] = per_month.get(month, ZERO) + row.amount
    return monthly


def _uncategorized(spend: list[AllocatedSpend], vendors: dict[str, Vendor]) -> list[UncategorizedInsight]:
    """The vouchers with the most spend not attributed to a category."""
    by_voucher: dict[str, list[AllocatedSpend]] = {}
    for row in spend:
        if not row.categorized:
            by_voucher.setdefault(row.voucher, []).append(row)
    amounts = {voucher: sum((row.amount for row in rows), ZERO) for voucher, rows in by_voucher.items()}
    ranked = sorted((v for v in amounts if amounts[v] > 0), key=lambda v: (-amounts[v], v))
    return [_uncategorized_voucher(by_voucher[voucher][0], amounts[voucher], vendors) for voucher in ranked[:LIST_SIZE]]


def _uncategorized_voucher(row: AllocatedSpend, amount: Decimal, vendors: dict[str, Vendor]) -> UncategorizedInsight:
    kind, _, key = row.voucher.partition(":")
    vendor = vendors.get(row.vendor_id) if row.vendor_id else None
    return UncategorizedInsight(
        voucher_id=key if kind == "v" else None,
        entry_id=key if kind == "e" else None,
        invoice_id=row.invoice_id,
        supplier_id=row.vendor_id,
        supplier_name=vendor.name if vendor else None,
        spent_on=row.spent_on,
        amount=amount,
    )


def _insight(vendor_id: str, vendors: dict[str, Vendor], amount: Decimal, **extra) -> SupplierInsight:
    return SupplierInsight(id=vendor_id, name=vendors[vendor_id].name, amount=amount, **extra)
