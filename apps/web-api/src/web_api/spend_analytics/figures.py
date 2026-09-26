"""Facts every spend report shares: sums by currency and period, suppliers' first invoices, work waiting."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable

from sqlalchemy import func, or_
from sqlmodel import Session, select

from web_api import config
from web_api.db.models import Invoice, InvoiceLine, Vendor
from web_api.db.models.enums import DocStatus, LineStatus
from web_api.reconcile import totals_agree
from web_api.schemas import AttentionCounts, PeriodRead, ReportPeriods

from .allocation import AllocatedSpend
from .periods import Period

ZERO = Decimal("0")


def by_currency(spend: Iterable[AllocatedSpend]) -> dict[str, list[AllocatedSpend]]:
    """The allocated spend grouped by base currency, currencies in alphabetical order."""
    grouped: dict[str, list[AllocatedSpend]] = {}
    for row in spend:
        grouped.setdefault(row.currency, []).append(row)
    return dict(sorted(grouped.items()))


def within(spend: Iterable[AllocatedSpend], period: Period) -> list[AllocatedSpend]:
    return [row for row in spend if period.contains(row.spent_on)]


def total(spend: Iterable[AllocatedSpend]) -> Decimal:
    return sum((row.amount for row in spend), ZERO)


def by_supplier(spend: Iterable[AllocatedSpend]) -> dict[str, Decimal]:
    """Spend per supplier; spend with no supplier is left out."""
    sums: dict[str, Decimal] = {}
    for row in spend:
        if row.vendor_id:
            sums[row.vendor_id] = sums.get(row.vendor_id, ZERO) + row.amount
    return sums


def report_periods(period: Period) -> ReportPeriods:
    comparison = period.comparison()
    return ReportPeriods(
        period=PeriodRead(start=period.start, end=period.end),
        comparison=PeriodRead(start=comparison.start, end=comparison.end),
    )


def first_invoice_dates(session: Session, company_ids: list[str]) -> dict[str, date]:
    """`{vendor_id: the date of its first invoice to these companies}`."""
    return dict(session.exec(
        select(Invoice.vendor_id, func.min(Invoice.invoice_date))
        .where(Invoice.company_id.in_(company_ids), Invoice.vendor_id.is_not(None),
               Invoice.invoice_date.is_not(None))
        .group_by(Invoice.vendor_id)
    ).all())


def vendor_names(session: Session, vendor_ids: Iterable[str]) -> dict[str, Vendor]:
    ids = set(vendor_ids)
    if not ids:
        return {}
    return {vendor.id: vendor for vendor in session.exec(select(Vendor).where(Vendor.id.in_(ids))).all()}


def attention_counts(session: Session, company_ids: list[str]) -> AttentionCounts:
    """Lines to review, documents that failed and totals that disagree, across the companies now."""
    needs_review = session.exec(
        select(func.count(InvoiceLine.id)).where(
            InvoiceLine.company_id.in_(company_ids),
            InvoiceLine.status == LineStatus.AI_CATEGORIZED.value,
            or_(
                InvoiceLine.confidence.is_(None),
                InvoiceLine.confidence < config.CATEGORIZATION_REVIEW_THRESHOLD,
            ),
        )
    ).one()
    failed = session.exec(
        select(func.count(Invoice.id)).where(
            Invoice.company_id.in_(company_ids), Invoice.doc_status == DocStatus.FAILED.value,
        )
    ).one()
    documented = session.exec(
        select(Invoice).where(
            Invoice.company_id.in_(company_ids),
            or_(Invoice.document_total.is_not(None), Invoice.document_subtotal.is_not(None)),
        )
    ).all()
    mismatched = sum(1 for invoice in documented if totals_agree(invoice) is False)
    return AttentionCounts(
        needs_review_lines=needs_review, failed_documents=failed, totals_mismatch=mismatched,
    )
