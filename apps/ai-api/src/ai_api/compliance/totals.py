"""A term's in-scope spend per month, with and without the supplier, recalculated from the lines."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, delete, exists, func
from sqlmodel import Session, col, select

from web_api.db.models import (
    AgreementFinding,
    AgreementScopeJudgement,
    AgreementTermSpend,
    FindingReviewStatus,
    Invoice,
    InvoiceLine,
)

from .pages import TermLines


def touched_months(session: Session, wanted: TermLines) -> set[date] | None:
    """The months with lines changed since `wanted.since`; None (every month) without it."""
    if wanted.since is None:
        return None
    days = session.exec(
        select(Invoice.invoice_date).distinct()
        .join(InvoiceLine, InvoiceLine.invoice_id == Invoice.id)
        .where(InvoiceLine.company_id == wanted.company_id,
               (col(InvoiceLine.changed_at) > wanted.since)
               | (col(Invoice.changed_at) > wanted.since))
    ).all()
    return {_month(day) for day in days if day is not None}


def recompute_totals(session: Session, wanted: TermLines, supplier_vendor_ids: set[str],
                     months: set[date] | None) -> None:
    """Replace the term's totals for `months` (every month when None) with sums of its in-scope
    lines; commits."""
    if months is not None and not months:
        return
    sums: dict[tuple[date, bool], list] = defaultdict(lambda: [Decimal(0), 0])
    for day, vendor_id, amount, lines in _daily(session, wanted, months):
        month = _month(day)
        if months is not None and month not in months:
            continue
        cell = sums[(month, vendor_id in supplier_vendor_ids)]
        cell[0] += Decimal(amount or 0)
        cell[1] += lines
    stale = delete(AgreementTermSpend).where(AgreementTermSpend.term_id == wanted.term_id)
    if months is not None:
        stale = stale.where(col(AgreementTermSpend.month).in_(months))
    session.exec(stale)
    session.add_all(AgreementTermSpend(term_id=wanted.term_id, month=month,
                                       from_supplier=from_supplier,
                                       amount=amount.quantize(Decimal("0.01")), lines=lines)
                    for (month, from_supplier), (amount, lines) in sums.items())
    session.commit()


def drop_totals(session: Session, term_ids: Iterable[str]) -> None:
    """Delete the totals of terms that are no longer confirmed; commits."""
    ids = list(term_ids)
    if ids:
        session.exec(delete(AgreementTermSpend).where(col(AgreementTermSpend.term_id).in_(ids)))
        session.commit()


def _daily(session: Session, wanted: TermLines, months: set[date] | None):
    base = func.coalesce(InvoiceLine.base_amount, InvoiceLine.amount)
    statement = (
        select(Invoice.invoice_date, Invoice.vendor_id, func.sum(base), func.count())
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .join(AgreementScopeJudgement, and_(
            AgreementScopeJudgement.question_key == InvoiceLine.item_key,
            AgreementScopeJudgement.term_id == wanted.term_id,
            AgreementScopeJudgement.term_key == wanted.term_key,
            AgreementScopeJudgement.in_scope == True,  # noqa: E712
        ))
        .where(InvoiceLine.company_id == wanted.company_id, Invoice.invoice_date >= wanted.start,
               base > 0, ~exists().where(
                   AgreementFinding.term_id == wanted.term_id,
                   AgreementFinding.invoice_line_id == InvoiceLine.id,
                   AgreementFinding.review_status == FindingReviewStatus.NOT_IN_SCOPE.value))
        .group_by(Invoice.invoice_date, Invoice.vendor_id)
    )
    if wanted.end is not None:
        statement = statement.where(Invoice.invoice_date <= wanted.end)
    if months is not None:
        statement = statement.where(Invoice.invoice_date >= min(months),
                                    Invoice.invoice_date < _next_month(max(months)))
    return session.exec(statement).all()


def _month(day: date) -> date:
    return day.replace(day=1)


def _next_month(month: date) -> date:
    return date(month.year + month.month // 12, month.month % 12 + 1, 1)
