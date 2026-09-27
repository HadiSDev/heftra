"""The dashboard's view of every agreement's open rule breaks in a period."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, col, select

from ..db.models import (
    Agreement,
    AgreementFinding,
    AgreementStatus,
    Company,
    FindingKind,
    FindingReviewStatus,
    FindingSeverity,
    Vendor,
)
from ..schemas.agreements import AgreementCompliance, OffContractSupplier
from ..spend_analytics.figures import report_periods
from ..spend_analytics.periods import Period

TOP_SUPPLIERS = 5


def agreement_compliance(session: Session, company_ids: list[str],
                         period: Period) -> AgreementCompliance:
    periods = report_periods(period)
    if not company_ids:
        return AgreementCompliance(**periods.model_dump())
    active = session.exec(
        select(Agreement.id).where(col(Agreement.company_id).in_(company_ids),
                                   Agreement.status == AgreementStatus.ACTIVE.value)
    ).first() is not None
    currencies = set(session.exec(
        select(Company.base_currency).where(col(Company.id).in_(company_ids))
    ).all())
    open_breaks = [
        col(AgreementFinding.company_id).in_(company_ids),
        AgreementFinding.severity == FindingSeverity.RULE_BREAK.value,
        AgreementFinding.review_status == FindingReviewStatus.OPEN.value,
        AgreementFinding.spent_on >= period.start,
        AgreementFinding.spent_on <= period.end,
    ]
    rows = session.exec(
        select(AgreementFinding.kind, func.count(AgreementFinding.id),
               func.sum(AgreementFinding.amount))
        .where(*open_breaks).group_by(AgreementFinding.kind)
    ).all()
    by_kind = {kind: (count, Decimal(amount or 0)) for kind, count, amount in rows}
    off_contract = by_kind.get(FindingKind.OFF_CONTRACT.value, (0, Decimal(0)))
    overcharge = by_kind.get(FindingKind.OVERCHARGE.value, (0, Decimal(0)))
    return AgreementCompliance(
        **periods.model_dump(),
        has_active_agreement=active,
        currency=next(iter(currencies)) if len(currencies) == 1 else None,
        open_rule_breaks=sum(count for count, _ in by_kind.values()),
        rule_break_amount=sum((amount for _, amount in by_kind.values()), Decimal(0)),
        off_contract_amount=off_contract[1],
        overcharge_amount=overcharge[1],
        top_suppliers=_top_suppliers(session, open_breaks),
    )


def _top_suppliers(session: Session, open_breaks: list) -> list[OffContractSupplier]:
    rows = session.exec(
        select(AgreementFinding.vendor_id, Vendor.name, func.sum(AgreementFinding.amount),
               func.count(AgreementFinding.id))
        .outerjoin(Vendor, Vendor.id == AgreementFinding.vendor_id)
        .where(*open_breaks, AgreementFinding.kind == FindingKind.OFF_CONTRACT.value)
        .group_by(AgreementFinding.vendor_id, Vendor.name)
        .order_by(func.sum(AgreementFinding.amount).desc())
        .limit(TOP_SUPPLIERS)
    ).all()
    return [OffContractSupplier(vendor_id=vendor_id, name=name or "Unknown supplier",
                                amount=Decimal(amount or 0), count=count)
            for vendor_id, name, amount, count in rows]
