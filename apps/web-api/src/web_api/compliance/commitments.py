"""How far each volume commitment has got in its current period."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, select

from ..db.models import (
    Agreement,
    AgreementFinding,
    AgreementTerm,
    AgreementTermKind,
    AgreementTermStatus,
)
from ..fx.service import FxService
from ..schemas.agreements import CommitmentProgress
from .periods import commitment_period

MONEY = Decimal("0.01")


def commitment_progress(session: Session, agreement: Agreement, base_currency: str,
                        today: date) -> list[CommitmentProgress]:
    """Spend to date, the pro-rata target and a linear forecast, in the company's base currency."""
    if agreement.starts_on is None:
        return []
    terms = session.exec(
        select(AgreementTerm).where(
            AgreementTerm.agreement_id == agreement.id,
            AgreementTerm.kind == AgreementTermKind.VOLUME_COMMITMENT.value,
            AgreementTerm.status == AgreementTermStatus.CONFIRMED.value,
        )
    ).all()
    fx = FxService.for_reads(session)
    progress = []
    for term in terms:
        if term.commitment_amount is None:
            continue
        period = commitment_period(term.commitment_period, agreement.starts_on,
                                   agreement.ends_on, today)
        rate = _rate(fx, term.currency or agreement.currency, base_currency, period.start)
        if rate is None:
            continue
        spent = _spent(session, term.id, period.start, period.end)
        elapsed = max(0, min((today - period.start).days + 1, period.days))
        committed = (term.commitment_amount * rate).quantize(MONEY)
        tiers = sorted((Decimal(str(tier["threshold"])) * rate).quantize(MONEY)
                       for tier in term.tiers or [])
        progress.append(CommitmentProgress(
            term_id=term.id,
            scope=term.scope,
            period_start=period.start,
            period_end=period.end,
            committed=committed,
            spent=spent,
            target_to_date=(committed * elapsed / period.days).quantize(MONEY),
            forecast=(spent * period.days / elapsed).quantize(MONEY) if elapsed else spent,
            tier_reached=max((tier for tier in tiers if tier <= spent), default=None),
            next_tier=min((tier for tier in tiers if tier > spent), default=None),
        ))
    return progress


def _spent(session: Session, term_id: str, start: date, end: date) -> Decimal:
    total = session.exec(
        select(func.sum(AgreementFinding.line_amount)).where(
            AgreementFinding.term_id == term_id,
            AgreementFinding.from_supplier == True,  # noqa: E712
            AgreementFinding.spent_on >= start,
            AgreementFinding.spent_on <= end,
        )
    ).one()
    return Decimal(total or 0).quantize(MONEY)


def _rate(fx: FxService, currency: str | None, base_currency: str, on: date) -> Decimal | None:
    if not currency or currency == base_currency:
        return Decimal(1)
    found = fx.get_rate(currency, base_currency, on)
    return found[0] if found else None
