"""Agreements as the list and their page show them."""
from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, col, select

from ..db.models import (
    Agreement,
    AgreementFinding,
    AgreementTerm,
    Company,
    File,
    FindingReviewStatus,
    FindingSeverity,
    Vendor,
)
from ..schemas.agreements import (
    AgreementFileRead,
    AgreementRead,
    AgreementSummaryRead,
    AgreementSupplier,
    TermRead,
)


def list_agreements(session: Session, company_ids: Sequence[str],
                    today: date) -> list[AgreementSummaryRead]:
    if not company_ids:
        return []
    agreements = session.exec(
        select(Agreement).where(col(Agreement.company_id).in_(company_ids))
        .order_by(col(Agreement.created_at).desc(), col(Agreement.id))
    ).all()
    return _summaries(session, agreements, today)


def agreement_read(session: Session, agreement: Agreement, today: date) -> AgreementRead:
    (summary,) = _summaries(session, [agreement], today)
    file_row = session.get(File, agreement.file_id)
    terms = session.exec(
        select(AgreementTerm).where(AgreementTerm.agreement_id == agreement.id)
        .order_by(col(AgreementTerm.created_at), col(AgreementTerm.id))
    ).all()
    return AgreementRead(
        **summary.model_dump(),
        supplier_vat_number=agreement.supplier_vat_number,
        supplier_website=agreement.supplier_website,
        summary=agreement.summary,
        read_at=agreement.read_at,
        file=AgreementFileRead(filename=file_row.filename if file_row else agreement.title,
                               file_size=int(file_row.file_size) if file_row and file_row.file_size
                               else None),
        terms=[TermRead.model_validate(term) for term in terms],
    )


def _summaries(session: Session, agreements: Sequence[Agreement],
               today: date) -> list[AgreementSummaryRead]:
    ids = [agreement.id for agreement in agreements]
    breaks = _open_rule_breaks(session, ids)
    vendors = _vendor_names(session, {a.vendor_id for a in agreements if a.vendor_id})
    currencies = dict(session.exec(
        select(Company.id, Company.base_currency)
        .where(col(Company.id).in_({a.company_id for a in agreements}))
    ).all()) if agreements else {}
    return [
        AgreementSummaryRead(
            id=agreement.id,
            company_id=agreement.company_id,
            title=agreement.title,
            reference=agreement.reference,
            supplier=AgreementSupplier(vendor_id=agreement.vendor_id,
                                       name=vendors[agreement.vendor_id])
            if agreement.vendor_id in vendors else None,
            supplier_name=agreement.supplier_name,
            starts_on=agreement.starts_on,
            ends_on=agreement.ends_on,
            currency=agreement.currency,
            status=agreement.status,
            expired=agreement.ends_on is not None and agreement.ends_on < today,
            read_error=agreement.read_error,
            analysed_at=agreement.analysed_at,
            created_at=agreement.created_at,
            open_rule_breaks=breaks.get(agreement.id, (0, Decimal(0)))[0],
            rule_break_amount=breaks.get(agreement.id, (0, Decimal(0)))[1],
            base_currency=currencies.get(agreement.company_id),
        )
        for agreement in agreements
    ]


def _open_rule_breaks(session: Session, ids: list[str]) -> dict[str, tuple[int, Decimal]]:
    if not ids:
        return {}
    rows = session.exec(
        select(AgreementFinding.agreement_id, func.count(AgreementFinding.id),
               func.sum(AgreementFinding.amount))
        .where(col(AgreementFinding.agreement_id).in_(ids),
               AgreementFinding.severity == FindingSeverity.RULE_BREAK.value,
               AgreementFinding.review_status == FindingReviewStatus.OPEN.value)
        .group_by(AgreementFinding.agreement_id)
    ).all()
    return {agreement_id: (count, Decimal(amount or 0)) for agreement_id, count, amount in rows}


def _vendor_names(session: Session, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    return dict(session.exec(select(Vendor.id, Vendor.name).where(col(Vendor.id).in_(ids))).all())
