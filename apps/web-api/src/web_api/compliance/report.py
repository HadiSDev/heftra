"""An agreement's report: totals, spend in scope, commitments and the findings."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, select

from ..db.models import (
    Agreement,
    AgreementFinding,
    AgreementTerm,
    AgreementTermSpend,
    AgreementTermStatus,
    Company,
    FindingReviewStatus,
)
from ..schemas.agreements import AgreementReport, FindingTotal
from .commitments import commitment_progress
from .findings import FindingSort, SortOrder, finding_page


def agreement_report(session: Session, agreement: Agreement, today: date, *,
                     kinds: list[str] | None, review_statuses: list[str] | None,
                     sort: FindingSort, order: SortOrder, page: int,
                     page_size: int) -> AgreementReport:
    base_currency = session.get(Company, agreement.company_id).base_currency
    in_scope, supplier = _spend_in_scope(session, agreement)
    return AgreementReport(
        agreement_id=agreement.id,
        analysed_at=agreement.analysed_at,
        currency=base_currency,
        in_scope_spend=in_scope,
        supplier_spend=supplier,
        totals=_open_totals(session, agreement.id),
        commitments=commitment_progress(session, agreement, base_currency, today),
        findings=finding_page(session, agreement.id, kinds=kinds,
                              review_statuses=review_statuses, sort=sort, order=order,
                              page=page, page_size=page_size),
    )


def _open_totals(session: Session, agreement_id: str) -> list[FindingTotal]:
    rows = session.exec(
        select(AgreementFinding.kind, AgreementFinding.severity, func.count(AgreementFinding.id),
               func.sum(AgreementFinding.amount))
        .where(AgreementFinding.agreement_id == agreement_id,
               AgreementFinding.review_status == FindingReviewStatus.OPEN.value)
        .group_by(AgreementFinding.kind, AgreementFinding.severity)
    ).all()
    return [FindingTotal(kind=kind, severity=severity, count=count, amount=Decimal(amount or 0))
            for kind, severity, count, amount in rows]


def _spend_in_scope(session: Session, agreement: Agreement) -> tuple[Decimal, Decimal]:
    """The spend in scope of the agreement's broadest confirmed term, and its share with the
    supplier, from the terms' monthly totals."""
    rows = session.exec(
        select(AgreementTermSpend.term_id, AgreementTermSpend.from_supplier,
               func.sum(AgreementTermSpend.amount))
        .join(AgreementTerm, AgreementTerm.id == AgreementTermSpend.term_id)
        .where(AgreementTerm.agreement_id == agreement.id,
               AgreementTerm.status == AgreementTermStatus.CONFIRMED.value)
        .group_by(AgreementTermSpend.term_id, AgreementTermSpend.from_supplier)
    ).all()
    per_term: dict[str, list[Decimal]] = {}
    for term_id, from_supplier, amount in rows:
        totals = per_term.setdefault(term_id, [Decimal(0), Decimal(0)])
        totals[0] += Decimal(amount or 0)
        if from_supplier:
            totals[1] += Decimal(amount or 0)
    if not per_term:
        return Decimal(0), Decimal(0)
    total, supplier = max(per_term.values(), key=lambda totals: totals[0])
    return total, supplier
