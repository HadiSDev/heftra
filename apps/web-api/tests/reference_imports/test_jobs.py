"""An import job's lifecycle, one unfinished job per kind, and restarts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

from web_api.db.models import ReferenceImportKind
from web_api.reference_imports.jobs import (
    INTERRUPTED,
    ImportInProgress,
    interrupt_unfinished,
    mark_running,
    mark_succeeded,
    recent_jobs,
    request_job,
)
from web_api.reference_imports.startup import interrupt_stale_jobs

PRICE_INDEX = ReferenceImportKind.PRICE_INDEX
WORKBOOK = ReferenceImportKind.FACTOR_WORKBOOK


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def test_a_job_runs_to_success(session):
    job = request_job(session, PRICE_INDEX, "CPIAUCSL", requested_by="u1")
    assert job.status == "queued"

    mark_running(session, job)
    mark_succeeded(session, job, {"months": 2})

    assert (job.status, job.result) == ("succeeded", {"months": 2})
    assert job.started_at is not None and job.finished_at is not None


def test_one_unfinished_job_per_kind(session):
    request_job(session, PRICE_INDEX, "CPIAUCSL", requested_by="u1")

    with pytest.raises(ImportInProgress):
        request_job(session, PRICE_INDEX, "CPIAUCSL", requested_by="u1")
    assert request_job(session, WORKBOOK, "ceda.xlsx", requested_by="u1").status == "queued"


def test_a_finished_job_frees_its_kind(session):
    job = request_job(session, PRICE_INDEX, "CPIAUCSL", requested_by="u1")
    mark_succeeded(session, job, {})

    assert request_job(session, PRICE_INDEX, "CPIAUCSL", requested_by="u1").status == "queued"


def test_unfinished_jobs_are_interrupted(session):
    queued = request_job(session, PRICE_INDEX, "CPIAUCSL", requested_by="u1")
    running = request_job(session, WORKBOOK, "ceda.xlsx", requested_by="u1")
    mark_running(session, running)

    assert interrupt_unfinished(session) == 2

    assert (queued.status, queued.error) == ("failed", INTERRUPTED)
    assert (running.status, running.error) == ("failed", INTERRUPTED)


def test_startup_interrupts_them_too(session, engine):
    job = request_job(session, PRICE_INDEX, "CPIAUCSL", requested_by="u1")

    interrupt_stale_jobs(engine)

    session.refresh(job)
    assert job.error == INTERRUPTED


def test_recent_jobs_come_newest_first(session):
    first = request_job(session, PRICE_INDEX, "CPIAUCSL", requested_by="u1")
    mark_succeeded(session, first, {})
    second = request_job(session, WORKBOOK, "ceda.xlsx", requested_by="u1")
    first.requested_at = datetime(2026, 9, 1, tzinfo=timezone.utc)
    second.requested_at = first.requested_at + timedelta(minutes=5)
    session.add_all([first, second])
    session.commit()

    assert [job.id for job in recent_jobs(session, 2)] == [second.id, first.id]
