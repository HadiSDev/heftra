"""When an agreement under review becomes active, and back."""
from __future__ import annotations

from sqlmodel import Session, select

from ..db.models import Agreement, AgreementStatus, AgreementTerm, AgreementTermStatus

_REVIEWABLE = {AgreementStatus.REVIEW.value, AgreementStatus.ACTIVE.value}


def settle_status(session: Session, agreement: Agreement) -> None:
    """Active once it has a supplier, a start date and a confirmed term; in review otherwise."""
    if agreement.status not in _REVIEWABLE:
        return
    confirmed = session.exec(
        select(AgreementTerm.id).where(
            AgreementTerm.agreement_id == agreement.id,
            AgreementTerm.status == AgreementTermStatus.CONFIRMED.value,
        )
    ).first()
    ready = agreement.vendor_id is not None and agreement.starts_on is not None and confirmed
    agreement.status = (AgreementStatus.ACTIVE if ready else AgreementStatus.REVIEW).value
    session.add(agreement)
