"""Queuing an analysis after spend changes, for companies with an active agreement."""
from __future__ import annotations

from sqlmodel import Session, select

from web_api.agreements.analysis import request_analysis
from web_api.db.models import SYSTEM_REQUESTER, Agreement, AgreementStatus, PipelineRunKind

SPEND_CHANGING_KINDS = {
    PipelineRunKind.SYNC.value,
    PipelineRunKind.READ_DOCUMENTS.value,
    PipelineRunKind.CATEGORIZE.value,
}


def queue_analysis_after(session: Session, kind: str, company_id: str) -> bool:
    """After a run that changes spend, ask for an analysis if an agreement is active."""
    if kind not in SPEND_CHANGING_KINDS:
        return False
    active = session.exec(
        select(Agreement.id).where(Agreement.company_id == company_id,
                                   Agreement.status == AgreementStatus.ACTIVE.value)
    ).first()
    if active is None:
        return False
    request_analysis(session, company_id, SYSTEM_REQUESTER)
    session.commit()
    return True
