"""Asking the worker to check a company's spend against its agreements."""
from __future__ import annotations

from sqlmodel import Session, col, select

from ..db.models import (
    Agreement,
    AgreementStatus,
    PipelineRun,
    PipelineRunKind,
    PipelineRunStatus,
)


def request_analysis(session: Session, company_id: str, requested_by: str) -> PipelineRun:
    """The company's queued analysis, or a new one queued behind any running; the caller commits."""
    existing = session.exec(
        select(PipelineRun).where(
            PipelineRun.company_id == company_id,
            PipelineRun.kind == PipelineRunKind.ANALYSE_AGREEMENTS.value,
            PipelineRun.status == PipelineRunStatus.QUEUED.value,
        )
    ).first()
    if existing is not None:
        return existing
    run = PipelineRun(company_id=company_id, kind=PipelineRunKind.ANALYSE_AGREEMENTS.value,
                      requested_by=requested_by)
    session.add(run)
    session.flush()
    return run


def request_full_analysis(session: Session, company_id: str, requested_by: str) -> PipelineRun:
    """Mark the company's active agreements for a full run and request one; the caller commits."""
    for agreement in session.exec(
        select(Agreement).where(Agreement.company_id == company_id,
                                Agreement.status == AgreementStatus.ACTIVE.value)
    ).all():
        agreement.full_analysis = True
        session.add(agreement)
    return request_analysis(session, company_id, requested_by)


def last_completed_analysis(session: Session, company_id: str) -> PipelineRun | None:
    """The company's analysis that succeeded last."""
    return session.exec(
        select(PipelineRun).where(
            PipelineRun.company_id == company_id,
            PipelineRun.kind == PipelineRunKind.ANALYSE_AGREEMENTS.value,
            PipelineRun.status == PipelineRunStatus.SUCCEEDED.value,
        ).order_by(col(PipelineRun.finished_at).desc(), col(PipelineRun.id).desc()).limit(1)
    ).first()


def latest_analysis(session: Session, company_id: str) -> PipelineRun | None:
    """The company's running analysis, else its queued one, else the one requested last."""
    runs = session.exec(
        select(PipelineRun).where(
            PipelineRun.company_id == company_id,
            PipelineRun.kind == PipelineRunKind.ANALYSE_AGREEMENTS.value,
        ).order_by(col(PipelineRun.requested_at).desc(), col(PipelineRun.id).desc()).limit(20)
    ).all()
    for status in (PipelineRunStatus.RUNNING.value, PipelineRunStatus.QUEUED.value):
        unfinished = next((run for run in runs if run.status == status), None)
        if unfinished is not None:
            return unfinished
    return runs[0] if runs else None
