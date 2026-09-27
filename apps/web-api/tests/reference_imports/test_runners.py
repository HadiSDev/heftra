"""Running workbook and price index jobs, including the failures that leave data unchanged."""
from __future__ import annotations

import pytest
from sqlmodel import Session, select

from ceda_workbook import write_workbook
from web_api.db.models import EmissionFactorSet, PriceIndexValue, ReferenceImportKind
from web_api.price_indices.fred import SeriesDownloadError
from web_api.reference_imports import runners
from web_api.reference_imports.jobs import request_job

FRED_CSV = "observation_date,CPIAUCSL\n2026-07-01,332.813\n2026-08-01,334.131\n"


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _workbook_job(session, activate=True):
    return request_job(session, ReferenceImportKind.FACTOR_WORKBOOK, "ceda.xlsx",
                       requested_by="u1", activate=activate)


def test_a_workbook_is_imported_activated_and_deleted(session, engine, tmp_path):
    path = write_workbook(tmp_path / "ceda.xlsx")
    job = _workbook_job(session)

    runners.run_workbook_job(engine, job.id, path)

    session.refresh(job)
    assert job.status == "succeeded"
    assert job.result["version"] == "CEDA 2025"
    assert (job.result["sectors"], job.result["factors"], job.result["active"]) == (2, 10, True)
    assert session.exec(select(EmissionFactorSet)).one().active is True
    assert not path.exists()


def test_a_workbook_missing_a_sheet_fails_and_changes_nothing(session, engine, tmp_path):
    path = write_workbook(tmp_path / "ceda.xlsx", leave_out="GHG_t_Raw")
    job = _workbook_job(session)

    runners.run_workbook_job(engine, job.id, path)

    session.refresh(job)
    assert job.status == "failed"
    assert "GHG_t_Raw" in job.error
    assert session.exec(select(EmissionFactorSet)).all() == []
    assert not path.exists()


def _index_job(session):
    return request_job(session, ReferenceImportKind.PRICE_INDEX, "CPIAUCSL", requested_by="u1")


def test_a_price_index_is_refreshed(session, engine, monkeypatch):
    monkeypatch.setattr(runners, "download_series_csv", lambda series: FRED_CSV)
    job = _index_job(session)

    runners.run_price_index_job(engine, job.id)

    session.refresh(job)
    assert (job.status, job.result) == ("succeeded", {"months": 2, "latest_month": "2026-08-01"})
    assert len(session.exec(select(PriceIndexValue)).all()) == 2


def test_a_failed_download_fails_the_job(session, engine, monkeypatch):
    def unreachable(series):
        raise SeriesDownloadError("downloading CPIAUCSL: timed out")

    monkeypatch.setattr(runners, "download_series_csv", unreachable)
    job = _index_job(session)

    runners.run_price_index_job(engine, job.id)

    session.refresh(job)
    assert (job.status, job.error) == ("failed", "downloading CPIAUCSL: timed out")
    assert session.exec(select(PriceIndexValue)).all() == []
