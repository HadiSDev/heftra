"""Emission factor status for everyone, and system-admin controls, over the API."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, select

from ceda_workbook import write_workbook
from emission_factors import Factors, consumer_prices
from web_api import config
from web_api.db.models import (
    AuditLog,
    EmissionFactorSet,
    EmissionSector,
    EmissionSectorSource,
    InvoiceLine,
    ReferenceDataImport,
    ReferenceImportKind,
)
from web_api.reference_imports import runners
from web_api.reference_imports.jobs import mark_running, request_job
from web_api_testkit import auth

_BASE = "/api/v1/admin/emission-factors"
_ADMIN = auth("tok_sysadmin")
FRED_CSV = "observation_date,CPIAUCSL\n2026-07-01,332.813\n2026-08-01,334.131\n"


@pytest.fixture
def uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "UPLOAD_TMP_DIR", str(tmp_path / "uploads"))
    (tmp_path / "uploads").mkdir()
    return tmp_path / "uploads"


def _sets(engine) -> dict[str, str]:
    with Session(engine) as s:
        current = Factors(s, version="CEDA 2025").factor_set
        older = Factors(s, version="CEDA 2024", active=False).factor_set
        return {"current": current.id, "older": older.id}


@pytest.mark.parametrize(("method", "path"), [
    ("post", "/sets/any/activate"),
    ("post", "/price-index/refresh"),
    ("post", "/workbooks"),
    ("get", "/imports"),
])
def test_an_organization_admin_is_refused_the_admin_actions(client, method, path):
    res = getattr(client, method)(f"{_BASE}{path}", headers=auth("tokA"))

    assert res.status_code == 403


def test_a_member_reads_the_status_with_only_their_own_companies(client, engine, seed):
    with Session(engine) as s:
        Factors(s, version="CEDA 2025")

    res = client.get(_BASE, headers=auth("tok_memberA"))

    assert res.status_code == 200
    body = res.json()
    assert [row["version"] for row in body["sets"]] == ["CEDA 2025"]
    assert [row["company_name"] for row in body["coverage"]] == ["Acme A"]


def test_a_system_admin_sees_every_companys_coverage(client, engine, seed):
    with Session(engine) as s:
        Factors(s)

    coverage = client.get(_BASE, headers=_ADMIN).json()["coverage"]

    assert {row["company_name"] for row in coverage} == {"Acme A", "Beta B"}


def test_the_status_lists_sets_active_first_with_their_counts(client, engine):
    with Session(engine) as s:
        Factors(s, version="CEDA 2024", active=False)
        factors = Factors(s, version="CEDA 2025")
        factors.sector("518200", "Hosting", {"DK": "0.5", "DE": "0.4"})

    body = client.get(_BASE, headers=_ADMIN).json()

    assert [(row["version"], row["active"]) for row in body["sets"]] == [
        ("CEDA 2025", True), ("CEDA 2024", False)]
    assert (body["sets"][0]["sectors"], body["sets"][0]["factors"]) == (1, 2)


def test_the_status_shows_the_price_index(client, engine):
    with Session(engine) as s:
        Factors(s)
        consumer_prices(s, m2026_08="334.131")

    (index,) = client.get(_BASE, headers=_ADMIN).json()["price_indices"]

    assert (index["series"], index["label"], index["currency"]) == ("CPIAUCSL", "US CPI", "USD")
    assert (index["months"], index["latest_month"]) == (13, "2026-08-01")
    assert (index["base_year"], Decimal(index["base_average"])) == (2023, Decimal("300"))


def test_a_price_index_not_yet_imported(client, engine):
    with Session(engine) as s:
        Factors(s)

    (index,) = client.get(_BASE, headers=_ADMIN).json()["price_indices"]

    assert (index["months"], index["latest_month"]) == (0, None)


def test_coverage_counts_each_companys_lines(client, engine, seed):
    with Session(engine) as s:
        factors = Factors(s)
        hosting = factors.sector("518200", "Hosting", {"DK": "0.5"})
        foreign = EmissionSector(classification="exiobase", code="X1", name="Other")
        s.add(foreign)
        s.commit()
        sectors = {
            seed["line_a1"]: (hosting.id, EmissionSectorSource.AI, Decimal("0.9")),
            seed["line_a2"]: (hosting.id, EmissionSectorSource.HUMAN, None),
            seed["line_b1"]: (hosting.id, EmissionSectorSource.AI, Decimal("0.3")),
        }
        for line_id, (sector_id, source, confidence) in sectors.items():
            line = s.get(InvoiceLine, line_id)
            line.emission_sector_id = sector_id
            line.emission_sector_source = source
            line.emission_sector_confidence = confidence
            s.add(line)
        s.add(InvoiceLine(company_id=seed["comp_b"], invoice_id=seed["inv_b"],
                          description="Old match", amount=Decimal("1"), status="verified",
                          sequence=1, emission_sector_id=foreign.id,
                          emission_sector_source=EmissionSectorSource.AI))
        s.commit()

    coverage = {row["company_name"]: row
                for row in client.get(_BASE, headers=_ADMIN).json()["coverage"]}

    acme = coverage["Acme A"]
    assert (acme["lines"], acme["ai"], acme["human"], acme["needs_review"],
            acme["unmatched"]) == (2, 1, 1, 0, 0)
    beta = coverage["Beta B"]
    assert (beta["organization_name"], beta["lines"], beta["ai"], beta["needs_review"],
            beta["unmatched"]) == ("Org B", 2, 1, 1, 1)


def test_activating_switches_the_set_and_audits_it(client, engine):
    ids = _sets(engine)

    res = client.post(f"{_BASE}/sets/{ids['older']}/activate", headers=_ADMIN)

    assert res.status_code == 200, res.text
    body = res.json()
    assert (body["factor_set"]["version"], body["factor_set"]["active"]) == ("CEDA 2024", True)
    assert (body["previous_version"], body["rematch_needed"]) == ("CEDA 2025", False)
    with Session(engine) as s:
        assert not s.get(EmissionFactorSet, ids["current"]).active
        assert s.exec(select(AuditLog).where(AuditLog.entity_id == ids["older"])).one()


def test_activating_the_active_set_is_a_no_op(client, engine):
    ids = _sets(engine)

    body = client.post(f"{_BASE}/sets/{ids['current']}/activate", headers=_ADMIN).json()

    assert body["previous_version"] is None
    with Session(engine) as s:
        assert s.exec(select(AuditLog)).all() == []


def test_activating_an_unknown_set_is_not_found(client):
    assert client.post(f"{_BASE}/sets/missing/activate", headers=_ADMIN).status_code == 404


def test_refreshing_cpi_runs_a_job(client, engine, monkeypatch):
    with Session(engine) as s:
        Factors(s)
    monkeypatch.setattr(runners, "download_series_csv", lambda series: FRED_CSV)

    res = client.post(f"{_BASE}/price-index/refresh", json={"series": "CPIAUCSL"},
                      headers=_ADMIN)

    assert res.status_code == 202, res.text
    assert (res.json()["status"], res.json()["kind"]) == ("queued", "price_index")
    (job,) = client.get(f"{_BASE}/imports", headers=_ADMIN).json()
    assert (job["status"], job["result"]["latest_month"]) == ("succeeded", "2026-08-01")
    assert job["requested_by_name"] == "Sys"


def test_a_series_no_set_uses_is_refused(client, engine):
    with Session(engine) as s:
        Factors(s)

    res = client.post(f"{_BASE}/price-index/refresh", json={"series": "PCEPI"}, headers=_ADMIN)

    assert res.status_code == 422


def test_uploading_a_workbook_imports_and_activates_it(client, engine, tmp_path, uploads):
    workbook = write_workbook(tmp_path / "ceda.xlsx").read_bytes()

    res = client.post(f"{_BASE}/workbooks", headers=_ADMIN, data={"activate": "true"},
                      files={"file": ("Open CEDA 2025.xlsx", workbook)})

    assert res.status_code == 202, res.text
    assert (res.json()["subject"], res.json()["activate"]) == ("Open CEDA 2025.xlsx", True)
    (job,) = client.get(f"{_BASE}/imports", headers=_ADMIN).json()
    assert job["status"] == "succeeded", job["error"]
    with Session(engine) as s:
        assert s.exec(select(EmissionFactorSet)).one().active is True
    assert list(uploads.iterdir()) == []


def test_a_workbook_over_the_limit_is_refused(client, engine, uploads, monkeypatch):
    monkeypatch.setattr(config, "EMISSION_WORKBOOK_MAX_BYTES", 10)

    res = client.post(f"{_BASE}/workbooks", headers=_ADMIN,
                      files={"file": ("ceda.xlsx", b"PK\x03\x04" + b"x" * 20)})

    assert res.status_code == 413
    assert list(uploads.iterdir()) == []


def test_a_pdf_is_refused(client, engine, uploads):
    res = client.post(f"{_BASE}/workbooks", headers=_ADMIN,
                      files={"file": ("invoice.pdf", b"%PDF-1.7")})

    assert res.status_code == 422
    with Session(engine) as s:
        assert s.exec(select(ReferenceDataImport)).all() == []


def test_a_second_upload_waits_for_the_first(client, engine, tmp_path, uploads):
    with Session(engine) as s:
        running = request_job(s, ReferenceImportKind.FACTOR_WORKBOOK, "first.xlsx",
                              requested_by="u1")
        mark_running(s, running)
    workbook = write_workbook(tmp_path / "ceda.xlsx").read_bytes()

    res = client.post(f"{_BASE}/workbooks", headers=_ADMIN,
                      files={"file": ("second.xlsx", workbook)})

    assert res.status_code == 409
    assert list(uploads.iterdir()) == []


def test_the_imports_list_is_limited(client, engine):
    with Session(engine) as s:
        for series in ("A", "B", "C"):
            job = ReferenceDataImport(kind="price_index", subject=series, requested_by="u1",
                                      status="succeeded")
            s.add(job)
            s.commit()

    jobs = client.get(f"{_BASE}/imports?limit=2", headers=_ADMIN).json()

    assert len(jobs) == 2
