"""The runs the demo company's data would have come from, finished, so the worker treats the
company as up to date: a scan requested at seeding isn't due again for a day."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session

from web_api.db.models import SYSTEM_REQUESTER, PipelineRun, PipelineRunKind, PipelineRunStatus

from ..ids import COMPANY_ID, demo_id

RUN_ORDER = (
    (PipelineRunKind.SYNC, timedelta(hours=3)),
    (PipelineRunKind.CATEGORIZE, timedelta(hours=2, minutes=40)),
    (PipelineRunKind.MATCH_EMISSIONS, timedelta(hours=2, minutes=10)),
    (PipelineRunKind.ANALYSE_AGREEMENTS, timedelta(hours=1, minutes=45)),
    (PipelineRunKind.SCAN_ALTERNATIVES, timedelta(minutes=6)),
)
RUN_LENGTH = timedelta(minutes=6)


def write_runs(session: Session, now: datetime) -> dict[str, PipelineRun]:
    """One succeeded run of each stage, the last ending at `now`; returns them by kind for their
    summaries to be filled in."""
    runs = {}
    for kind, before in RUN_ORDER:
        requested = now - before
        run = PipelineRun(
            id=demo_id("pipeline-run", kind.value), company_id=COMPANY_ID, kind=kind.value,
            status=PipelineRunStatus.SUCCEEDED.value, requested_by=SYSTEM_REQUESTER,
            requested_at=requested, started_at=requested, finished_at=requested + RUN_LENGTH,
            summary={})
        session.add(run)
        runs[kind.value] = run
    session.flush()
    return runs


def summarize(session: Session, run: PipelineRun, summary: dict) -> None:
    run.summary = summary
    session.add(run)
