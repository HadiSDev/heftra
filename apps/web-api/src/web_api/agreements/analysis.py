"""Asking the worker to check a company's spend against its agreements."""
from __future__ import annotations

from sqlmodel import Session, select

from ..db.models import PipelineRun, PipelineRunKind, PipelineRunStatus


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
