"""An agreement's findings as the report lists them, rule breaks first."""
from __future__ import annotations

from sqlalchemy import case, func
from sqlmodel import Session, col, select

from ..db.models import (
    AgreementFinding,
    AgreementTerm,
    ErpEntry,
    FindingSeverity,
    InvoiceLine,
    User,
    Vendor,
)
from ..schemas.agreements import FindingRead
from ..schemas.common import Page

SEVERITY_ORDER = case(
    (AgreementFinding.severity == FindingSeverity.RULE_BREAK.value, 0),
    (AgreementFinding.severity == FindingSeverity.WARNING.value, 1),
    else_=2,
)


def finding_page(session: Session, agreement_id: str, *, kinds: list[str] | None,
                 review_statuses: list[str] | None, page: int,
                 page_size: int) -> Page[FindingRead]:
    conditions = [AgreementFinding.agreement_id == agreement_id]
    if kinds:
        conditions.append(col(AgreementFinding.kind).in_(kinds))
    if review_statuses:
        conditions.append(col(AgreementFinding.review_status).in_(review_statuses))
    total = session.exec(select(func.count(AgreementFinding.id)).where(*conditions)).one()
    rows = session.exec(
        _finding_rows().where(*conditions)
        .order_by(SEVERITY_ORDER, col(AgreementFinding.amount).desc(),
                  col(AgreementFinding.spent_on).desc(), col(AgreementFinding.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(items=_reads(session, rows), page=page, page_size=page_size, total=total)


def finding_read(session: Session, finding_id: str) -> FindingRead:
    rows = session.exec(_finding_rows().where(AgreementFinding.id == finding_id)).all()
    (read,) = _reads(session, rows)
    return read


def _finding_rows():
    return (
        select(AgreementFinding, AgreementTerm, InvoiceLine.item_name, InvoiceLine.description,
               Vendor.name, User.name)
        .join(AgreementTerm, AgreementTerm.id == AgreementFinding.term_id)
        .join(InvoiceLine, InvoiceLine.id == AgreementFinding.invoice_line_id)
        .outerjoin(Vendor, Vendor.id == AgreementFinding.vendor_id)
        .outerjoin(User, User.id == AgreementFinding.reviewed_by)
    )


def _reads(session: Session, rows) -> list[FindingRead]:
    vouchers = _voucher_ids(session, {row[0].invoice_id for row in rows})
    return [
        FindingRead(
            id=finding.id,
            agreement_id=finding.agreement_id,
            term_id=finding.term_id,
            term_kind=term.kind,
            term_scope=term.scope,
            term_conditions=term.conditions,
            kind=finding.kind,
            severity=finding.severity,
            amount=finding.amount,
            line_amount=finding.line_amount,
            currency=finding.currency,
            expected=finding.expected,
            actual=finding.actual,
            quantity=finding.quantity,
            reason=finding.reason,
            judge_confidence=finding.judge_confidence,
            spent_on=finding.spent_on,
            invoice_line_id=finding.invoice_line_id,
            invoice_id=finding.invoice_id,
            voucher_id=vouchers.get(finding.invoice_id),
            item=item_name or description,
            supplier_name=supplier_name,
            from_supplier=finding.from_supplier,
            review_status=finding.review_status,
            review_note=finding.review_note,
            reviewed_by_name=reviewer_name,
            reviewed_at=finding.reviewed_at,
        )
        for finding, term, item_name, description, supplier_name, reviewer_name in rows
    ]


def _voucher_ids(session: Session, invoice_ids: set[str]) -> dict[str, str]:
    if not invoice_ids:
        return {}
    rows = session.exec(
        select(ErpEntry.source_invoice_id, ErpEntry.voucher_id)
        .where(col(ErpEntry.source_invoice_id).in_(invoice_ids),
               col(ErpEntry.voucher_id).is_not(None))
    ).all()
    return {invoice_id: voucher_id for invoice_id, voucher_id in rows if invoice_id}
