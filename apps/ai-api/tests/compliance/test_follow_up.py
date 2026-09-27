"""An analysis follows runs that change spend, for companies with an active agreement."""
from __future__ import annotations

from sqlmodel import Session, select

from agreement_books import Books
from ai_api.compliance.follow_up import queue_analysis_after
from ai_api.worker.executors import EXECUTORS
from web_api.db.models import AgreementStatus, PipelineRun


def _runs(session) -> list[PipelineRun]:
    return list(session.exec(select(PipelineRun)).all())


def test_a_sync_queues_one_analysis(engine):
    with Session(engine) as s:
        books = Books(s)
        books.agreement()

        assert queue_analysis_after(s, "sync", books.company.id) is True
        assert queue_analysis_after(s, "categorize", books.company.id) is True

        (run,) = _runs(s)
        assert (run.kind, run.requested_by, run.status) == ("analyse_agreements", "system",
                                                           "queued")


def test_no_active_agreement_no_analysis(engine):
    with Session(engine) as s:
        books = Books(s)
        agreement = books.agreement()
        agreement.status = AgreementStatus.REVIEW.value
        s.add(agreement)
        s.commit()

        assert queue_analysis_after(s, "sync", books.company.id) is False
        assert _runs(s) == []


def test_other_runs_don_t_queue_one(engine):
    with Session(engine) as s:
        books = Books(s)
        books.agreement()

        assert queue_analysis_after(s, "match_emissions", books.company.id) is False


def test_the_worker_can_run_an_analysis():
    assert "analyse_agreements" in EXECUTORS
