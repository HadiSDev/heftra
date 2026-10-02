"""Queueing each company's background scan for alternatives once its interval has passed."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.engine import Engine
from sqlmodel import Session, col, func, select

from web_api.db.models import SYSTEM_REQUESTER, Company, PipelineRun, PipelineRunKind

from .. import config

SCAN = PipelineRunKind.SCAN_ALTERNATIVES.value


def queue_due_scans(engine: Engine, *, now: datetime | None = None) -> bool:
    """Queue a scan for each active company whose last one was requested more than
    `ALTERNATIVES_SCAN_INTERVAL_HOURS` ago; returns whether any was queued. Off unless
    `ALTERNATIVES_SCAN_ENABLED`."""
    if not config.ALTERNATIVES_SCAN_ENABLED:
        return False
    now = now or datetime.now(timezone.utc)
    due_before = now - timedelta(hours=config.ALTERNATIVES_SCAN_INTERVAL_HOURS)
    with Session(engine) as session:
        last = dict(session.exec(
            select(PipelineRun.company_id, func.max(PipelineRun.requested_at))
            .where(PipelineRun.kind == SCAN).group_by(PipelineRun.company_id)).all())
        due = [company_id for company_id in session.exec(
            select(Company.id).where(col(Company.is_active).is_(True))).all()
            if last.get(company_id) is None or _aware(last[company_id]) < due_before]
        for company_id in due:
            session.add(PipelineRun(company_id=company_id, kind=SCAN,
                                    requested_by=SYSTEM_REQUESTER, requested_at=now))
        session.commit()
    return bool(due)


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
