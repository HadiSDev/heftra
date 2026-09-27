"""An agreement's report: totals, spend in scope, commitments and the findings."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, select

from ..db.models import (
    Agreement,
    AgreementFinding,
    Company,
    FindingReviewStatus,
)
from ..schemas.agreements import AgreementReport, FindingTotal
from .commitments import commitment_progress
from .findings import finding_page


def agreement_report(session: Session, agreement: Agreement, today: date, *,
                     kinds: list[str] | None, review_statuses: list[str] | None, page: int,
                     page_size: int) -> AgreementReport:
    base_currency = session.get(Company, agreement.company_id).base_currency
    in_scope, supplier = _spend_in_scope(session, agreement.id)
    return AgreementReport(
        agreement_id=agreement.id,
        analysed_at=agreement.analysed_at,
        currency=base_currency,
        in_scope_spend=in_scope,
        supplier_spend=supplier,
        totals=_open_totals(session, agreement.id),
        commitments=commitment_progress(session, agreement, base_currency, today),
        findings=finding_page(session, agreement.id, kinds=kinds,
                              review_statuses=review_statuses, page=page, page_size=page_size),
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


def _spend_in_scope(session: Session, agreement_id: str) -> tuple[Decimal, Decimal]:
    """Each in-scope line counted once: all of them, and those with the agreement's supplier."""
    lines = session.exec(
        select(AgreementFinding.invoice_line_id, AgreementFinding.line_amount,
               AgreementFinding.from_supplier)
        .where(AgreementFinding.agreement_id == agreement_id,
               AgreementFinding.review_status != FindingReviewStatus.NOT_IN_SCOPE.value)
        .distinct()
    ).all()
    seen: dict[str, tuple[Decimal, bool]] = {}
    for line_id, amount, from_supplier in lines:
        seen[line_id] = (Decimal(amount), from_supplier)
    total = sum((amount for amount, _ in seen.values()), Decimal(0))
    supplier = sum((amount for amount, own in seen.values() if own), Decimal(0))
    return total, supplier
