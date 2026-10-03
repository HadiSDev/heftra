"""An agreement's findings as the report lists them, rule breaks first unless sorted otherwise."""
from __future__ import annotations

from typing import Literal

from sqlalchemy import case, func, nulls_last
from sqlmodel import Session, col, select

from ..db.models import (
    AgreementFinding,
    AgreementTerm,
    FindingSeverity,
    InvoiceLine,
    User,
    Vendor,
)
from ..schemas.agreements import FindingRead
from ..schemas.common import Page
from ..vouchers.invoices import voucher_ids

FindingSort = Literal["severity", "amount", "spent_on", "supplier", "item"]
SortOrder = Literal["asc", "desc"]

SEVERITY_RANK = case(
    (AgreementFinding.severity == FindingSeverity.RULE_BREAK.value, 2),
    (AgreementFinding.severity == FindingSeverity.WARNING.value, 1),
    else_=0,
)

_SORT_COLUMNS = {
    "severity": SEVERITY_RANK,
    "amount": col(AgreementFinding.amount),
    "spent_on": col(AgreementFinding.spent_on),
    "supplier": func.lower(Vendor.name),
    "item": func.lower(func.coalesce(InvoiceLine.item_name, InvoiceLine.description)),
}

_DEFAULT_ORDER = (
    SEVERITY_RANK.desc(),
    col(AgreementFinding.amount).desc(),
    nulls_last(col(AgreementFinding.spent_on).desc()),
    col(AgreementFinding.id),
)


def default_order(sort: FindingSort) -> SortOrder:
    """The order a column sorts in when first chosen: text A–Z, the rest largest, newest or
    most severe first."""
    return "asc" if sort in ("supplier", "item") else "desc"


def finding_page(session: Session, agreement_id: str, *, kinds: list[str] | None,
                 review_statuses: list[str] | None, sort: FindingSort, order: SortOrder,
                 page: int, page_size: int) -> Page[FindingRead]:
    conditions = [AgreementFinding.agreement_id == agreement_id]
    if kinds:
        conditions.append(col(AgreementFinding.kind).in_(kinds))
    if review_statuses:
        conditions.append(col(AgreementFinding.review_status).in_(review_statuses))
    total = session.exec(select(func.count(AgreementFinding.id)).where(*conditions)).one()
    column = _SORT_COLUMNS[sort]
    direction = column.asc() if order == "asc" else column.desc()
    rows = session.exec(
        _finding_rows().where(*conditions)
        .order_by(nulls_last(direction), *_DEFAULT_ORDER)
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
    vouchers = voucher_ids(session, {row[0].invoice_id for row in rows})
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
