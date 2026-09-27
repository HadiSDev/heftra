"""An import job's lifecycle: requested, running, and then succeeded or failed."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, col, select

from ..db.models import ReferenceDataImport, ReferenceImportKind, ReferenceImportStatus

INTERRUPTED = "Interrupted by a restart"

UNFINISHED = (ReferenceImportStatus.QUEUED.value, ReferenceImportStatus.RUNNING.value)


class ImportInProgress(Exception):
    """A job of the same kind is already queued or running."""


def ensure_idle(session: Session, kind: ReferenceImportKind) -> None:
    """Raise `ImportInProgress` while a job of `kind` is queued or running."""
    busy = session.exec(
        select(ReferenceDataImport.id).where(
            ReferenceDataImport.kind == kind.value,
            col(ReferenceDataImport.status).in_(UNFINISHED),
        )
    ).first()
    if busy is not None:
        raise ImportInProgress(kind.value)


def request_job(session: Session, kind: ReferenceImportKind, subject: str, *,
                requested_by: str, activate: bool = False) -> ReferenceDataImport:
    """A queued job, committed; refused while another of its kind is unfinished."""
    ensure_idle(session, kind)
    job = ReferenceDataImport(kind=kind.value, subject=subject, activate=activate,
                              requested_by=requested_by)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def mark_running(session: Session, job: ReferenceDataImport) -> None:
    job.status = ReferenceImportStatus.RUNNING.value
    job.started_at = _now()
    session.add(job)
    session.commit()


def mark_succeeded(session: Session, job: ReferenceDataImport, result: dict) -> None:
    job.status = ReferenceImportStatus.SUCCEEDED.value
    job.result = result
    job.finished_at = _now()
    session.add(job)
    session.commit()


def mark_failed(session: Session, job: ReferenceDataImport, error: str) -> None:
    job.status = ReferenceImportStatus.FAILED.value
    job.error = error
    job.finished_at = _now()
    session.add(job)
    session.commit()


def interrupt_unfinished(session: Session) -> int:
    """Fail every queued or running job, which no process is running any more."""
    jobs = session.exec(
        select(ReferenceDataImport).where(col(ReferenceDataImport.status).in_(UNFINISHED))
    ).all()
    for job in jobs:
        mark_failed(session, job, INTERRUPTED)
    return len(jobs)


def recent_jobs(session: Session, limit: int) -> list[ReferenceDataImport]:
    return list(session.exec(
        select(ReferenceDataImport)
        .order_by(col(ReferenceDataImport.requested_at).desc(), col(ReferenceDataImport.id))
        .limit(limit)
    ).all())


def _now() -> datetime:
    return datetime.now(timezone.utc)
