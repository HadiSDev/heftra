"""Uploading, listing, correcting, reading again and deleting agreements over the API."""
from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import Session, select

from agreement_records import agreement, finding, supplier, term
from web_api import config
from web_api.db.models import (
    Agreement,
    AgreementFinding,
    AgreementStatus,
    AgreementTerm,
    AgreementTermStatus,
    AuditLog,
    File,
    FindingKind,
    PipelineRun,
)
from web_api.storage.dependency import get_file_store
from web_api.storage.errors import StorageUnavailable
from web_api.storage.memory import MemoryFileStore
from web_api_testkit import auth

PDF = b"%PDF-1.7\n" + b"x" * 200


@pytest.fixture
def store(client) -> MemoryFileStore:
    memory = MemoryFileStore()
    client.app.dependency_overrides[get_file_store] = lambda: memory
    return memory


def _upload(client, company_id, *, token="tokA", name="Atea framework 2026.pdf", data=PDF):
    return client.post(f"/api/v1/companies/{company_id}/agreements", headers=auth(token),
                       files={"file": (name, data, "application/pdf")})


def test_a_manager_uploads_an_agreement(client, engine, seed, store):
    res = _upload(client, seed["comp_a"])

    assert res.status_code == 201, res.text
    body = res.json()
    assert (body["status"], body["title"]) == ("pending", "Atea framework 2026")
    assert body["file"]["filename"] == "Atea framework 2026.pdf"
    (key,) = store.objects
    assert key.startswith(f"companies/{seed['comp_a']}/agreements/{body['id']}/")
    with Session(engine) as s:
        assert s.exec(select(AuditLog).where(AuditLog.entity_id == body["id"])).one()


def test_a_viewer_cannot_upload(client, seed, store):
    assert _upload(client, seed["comp_a"], token="tok_viewerA").status_code == 403
    assert store.objects == {}


def test_another_organizations_company_is_not_found(client, seed, store):
    assert _upload(client, seed["comp_b"]).status_code == 404


def test_only_pdfs_are_accepted(client, seed, store):
    res = _upload(client, seed["comp_a"], name="terms.docx", data=b"PK\x03\x04")

    assert res.status_code == 422
    assert store.objects == {}


def test_a_file_over_the_limit_is_refused(client, seed, store, monkeypatch):
    monkeypatch.setattr(config, "AGREEMENT_MAX_BYTES", 50)

    assert _upload(client, seed["comp_a"]).status_code == 413


def test_storage_down_leaves_nothing_behind(client, engine, seed, store, monkeypatch):
    async def down(key, data, content_type):
        raise StorageUnavailable("connection refused")

    monkeypatch.setattr(store, "put", down)

    assert _upload(client, seed["comp_a"]).status_code == 503
    with Session(engine) as s:
        assert s.exec(select(Agreement)).all() == []
        assert s.exec(select(File).where(File.file_type == "agreement_pdf")).all() == []


def test_the_list_shows_open_rule_breaks(client, engine, seed):
    with Session(engine) as s:
        vendor = supplier(s)
        record = agreement(s, seed["comp_a"], vendor=vendor)
        rule = term(s, record.id)
        finding(s, agreement=record, term=rule, line_id=seed["line_a1"], invoice_id=seed["inv_a"],
                amount="9200.00")
        reviewed = finding(s, agreement=record, term=rule, line_id=seed["line_a2"],
                           invoice_id=seed["inv_a"], amount="500.00")
        reviewed.review_status = "exception"
        s.add(reviewed)
        s.commit()

    (row,) = client.get("/api/v1/agreements", headers=auth("tokA")).json()

    assert (row["open_rule_breaks"], row["rule_break_amount"]) == (1, "9200.00")
    assert row["supplier"]["name"] == "Atea A/S"


def test_the_document_is_streamed(client, engine, seed, store):
    agreement_id = _upload(client, seed["comp_a"]).json()["id"]

    res = client.get(f"/api/v1/agreements/{agreement_id}/document", headers=auth("tokA"))

    assert res.status_code == 200
    assert res.content == PDF
    assert res.headers["content-type"] == "application/pdf"


def test_another_organization_cannot_see_an_agreement(client, engine, seed, store):
    agreement_id = _upload(client, seed["comp_a"]).json()["id"]

    for path in ("", "/document", "/report"):
        assert client.get(f"/api/v1/agreements/{agreement_id}{path}",
                          headers=auth("tokB")).status_code == 404


def test_the_header_is_corrected_and_the_agreement_becomes_active(client, engine, seed):
    with Session(engine) as s:
        vendor = supplier(s)
        record = agreement(s, seed["comp_a"], status=AgreementStatus.REVIEW, starts_on=None)
        agreement_id, vendor_id = record.id, vendor.id
        term(s, agreement_id)

    res = client.patch(f"/api/v1/agreements/{agreement_id}", headers=auth("tokA"),
                       json={"vendor_id": vendor_id, "starts_on": "2026-01-01",
                             "ends_on": "2027-12-31"})

    assert res.status_code == 200, res.text
    assert (res.json()["status"], res.json()["supplier"]["vendor_id"]) == ("active", vendor_id)
    with Session(engine) as s:
        assert s.exec(select(PipelineRun).where(PipelineRun.kind == "analyse_agreements")).one()


def test_an_agreement_cannot_end_before_it_starts(client, engine, seed):
    with Session(engine) as s:
        record = agreement(s, seed["comp_a"])

    res = client.patch(f"/api/v1/agreements/{record.id}", headers=auth("tokA"),
                       json={"starts_on": "2026-01-01", "ends_on": "2025-01-01"})

    assert res.status_code == 422


def test_reading_again_queues_the_document(client, engine, seed):
    with Session(engine) as s:
        record = agreement(s, seed["comp_a"], status=AgreementStatus.FAILED)
        agreement_id = record.id
        record.read_error = "timed out"
        record.read_attempts = 3
        s.add(record)
        s.commit()

    body = client.post(f"/api/v1/agreements/{agreement_id}/read", headers=auth("tokA")).json()

    assert (body["status"], body["read_error"]) == ("pending", None)


def test_deleting_removes_the_agreement_and_its_file(client, engine, seed, store):
    agreement_id = _upload(client, seed["comp_a"]).json()["id"]
    with Session(engine) as s:
        rule = term(s, agreement_id)
        record = s.get(Agreement, agreement_id)
        finding(s, agreement=record, term=rule, line_id=seed["line_a1"], invoice_id=seed["inv_a"])

    res = client.delete(f"/api/v1/agreements/{agreement_id}", headers=auth("tokA"))

    assert res.status_code == 204
    assert store.objects == {}
    with Session(engine) as s:
        assert s.get(Agreement, agreement_id) is None
        assert s.exec(select(AgreementTerm)).all() == []
        assert s.exec(select(AgreementFinding)).all() == []


def test_a_manager_asks_for_analysis_once(client, engine, seed):
    first = client.post(f"/api/v1/companies/{seed['comp_a']}/agreements/analyse",
                        headers=auth("tokA"))
    second = client.post(f"/api/v1/companies/{seed['comp_a']}/agreements/analyse",
                         headers=auth("tokA"))

    assert first.status_code == 202
    assert first.json()["id"] == second.json()["id"]
    assert client.post(f"/api/v1/companies/{seed['comp_a']}/agreements/analyse",
                       headers=auth("tok_viewerA")).status_code == 403


def test_the_period_s_rule_breaks_reach_the_dashboard(client, engine, seed):
    with Session(engine) as s:
        vendor = supplier(s)
        other = supplier(s, name="Proshop", vat="DK87654321")
        record = agreement(s, seed["comp_a"], vendor=vendor)
        rule = term(s, record.id)
        finding(s, agreement=record, term=rule, line_id=seed["line_a1"], invoice_id=seed["inv_a"],
                amount="9200.00", vendor_id=other.id, spent_on=date(2025, 7, 1))
        finding(s, agreement=record, term=rule, line_id=seed["line_a2"], invoice_id=seed["inv_a"],
                kind=FindingKind.OVERCHARGE, amount="1200.00", vendor_id=vendor.id,
                from_supplier=True, spent_on=date(2025, 7, 2))

    body = client.get("/api/v1/reports/agreement-compliance", headers=auth("tokA"),
                      params={"from": "2025-07-01", "to": "2025-07-31"}).json()

    assert body["has_active_agreement"] is True
    assert (body["open_rule_breaks"], body["rule_break_amount"]) == (2, "10400.00")
    assert (body["off_contract_amount"], body["overcharge_amount"]) == ("9200.00", "1200.00")
    assert [(row["name"], row["amount"]) for row in body["top_suppliers"]] == [
        ("Proshop", "9200.00")]


def test_deleting_the_company_deletes_its_agreements(client, engine, seed, store):
    agreement_id = _upload(client, seed["comp_a"]).json()["id"]

    res = client.delete(f"/api/v1/companies/{seed['comp_a']}?confirm=true",
                        headers=auth("tok_sysadmin"))

    assert res.status_code == 200, res.text
    with Session(engine) as s:
        assert s.get(Agreement, agreement_id) is None
