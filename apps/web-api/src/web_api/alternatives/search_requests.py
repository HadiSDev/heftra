"""Asking the worker to find an item's alternatives."""
from __future__ import annotations

from sqlmodel import Session

from ..db.models import CompanyItem, PipelineRun, PipelineRunKind, PipelineRunStatus
from .reads import searching


def request_item_search(session: Session, item: CompanyItem, requested_by: str) -> PipelineRun:
    """The item's queued search, or a new one; the caller commits."""
    existing = searching(session, item)
    if existing is not None and existing.status == PipelineRunStatus.QUEUED.value:
        return existing
    run = PipelineRun(company_id=item.company_id, kind=PipelineRunKind.FIND_ALTERNATIVES.value,
                      requested_by=requested_by, params={"item_id": item.id})
    session.add(run)
    session.flush()
    return run
