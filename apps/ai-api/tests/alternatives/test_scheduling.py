"""Background scans queued once their interval has passed, and claimed after other runs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

from ai_api import config
from ai_api.alternatives.scheduling import queue_due_scans
from ai_api.worker.claims import claim_next
from alternatives_books import Shelves
from web_api.db.models import PipelineRun

NOW = datetime(2026, 6, 1, 12, tzinfo=timezone.utc)


@pytest.fixture
def company(engine):
    with Session(engine) as session:
        shelves = Shelves(session)
        inactive = shelves.company(shelves.organization("Gone"), "Gone")
        inactive.is_active = False
        session.add(inactive)
        session.commit()
        return shelves.company(shelves.organization("Acme")).id


def _scans(engine) -> list[PipelineRun]:
    with Session(engine) as session:
        return list(session.exec(select(PipelineRun)).all())


def test_nothing_is_queued_unless_scans_are_on(engine, company):
    assert queue_due_scans(engine, now=NOW) is False
    assert _scans(engine) == []


def test_an_active_company_gets_one_scan_per_interval(engine, company, monkeypatch):
    monkeypatch.setattr(config, "ALTERNATIVES_SCAN_ENABLED", True)

    assert queue_due_scans(engine, now=NOW) is True
    assert queue_due_scans(engine, now=NOW + timedelta(hours=1)) is False
    assert queue_due_scans(engine, now=NOW + timedelta(hours=25)) is True

    scans = _scans(engine)
    assert {scan.company_id for scan in scans} == {company}
    assert len(scans) == 2


def test_a_scan_is_claimed_after_other_runs(engine, company):
    with Session(engine) as session:
        session.add(PipelineRun(company_id=company, kind="scan_alternatives",
                                requested_by="system", requested_at=NOW))
        session.add(PipelineRun(company_id=company, kind="analyse_agreements",
                                requested_by="user", requested_at=NOW + timedelta(minutes=5)))
        session.commit()

        assert claim_next(session).kind == "analyse_agreements"
        assert claim_next(session).kind == "scan_alternatives"
