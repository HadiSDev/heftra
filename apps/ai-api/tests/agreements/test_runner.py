"""A pending agreement read from storage into a header and draft terms, or failed with its error."""
from __future__ import annotations

import json

import pytest
from sqlmodel import Session, select

from agreement_pdf import FRAMEWORK, agreement_pdf
from ai_api import config
from ai_api.agreements.runner import read_pending
from web_api.db.models import (
    Agreement,
    AgreementTerm,
    AgreementTermStatus,
    File,
    Invoice,
    Vendor,
)
from web_api.storage.blocking import run_blocking
from web_api.storage.memory import MemoryFileStore

KEY = "companies/c/agreements/a/file.pdf"
HEADER = {"title": "Framework agreement FA-2026-17", "reference": "FA-2026-17",
          "supplier_name": "Atea A/S", "supplier_vat_number": "12345678",
          "supplier_country_code": "DK", "starts_on": "2026-01-01", "ends_on": "2027-12-31",
          "currency": "DKK"}
TERMS = [
    {"kind": "preferred_supplier", "scope": "IT equipment",
     "conditions": "when available from stock",
     "quote": "IT equipment shall be purchased from Atea when available from stock.", "page": 2},
    {"kind": "agreed_price", "scope": "Laptops", "item": "Lenovo ThinkPad T14 Gen 5",
     "unit": "unit", "unit_price": "8.000,00", "currency": "DKK",
     "quote": "Lenovo ThinkPad T14 Gen 5: DKK 8.000,00 per unit.", "page": 3},
]


class Model:
    def __init__(self, terms=TERMS, fail: bool = False) -> None:
        self.calls = 0
        self.terms = terms
        self.fail = fail

    def __call__(self, messages) -> str:
        self.calls += 1
        if self.fail:
            raise RuntimeError("model down")
        if self.calls == 1:
            return json.dumps(HEADER)
        return json.dumps({"terms": self.terms if self.calls == 2 else []})


@pytest.fixture
def one_part(monkeypatch):
    monkeypatch.setattr(config, "AGREEMENT_CHUNK_PAGES", 10)


@pytest.fixture
def store() -> MemoryFileStore:
    memory = MemoryFileStore()
    run_blocking(memory.put(KEY, agreement_pdf(FRAMEWORK), "application/pdf"))
    return memory


def _no_suggestions(session, company_id):
    return lambda scope: ["category-1"]


def _pending(engine, company_id: str, *, with_supplier: bool = True) -> str:
    with Session(engine) as s:
        if with_supplier:
            vendor = Vendor(name="Atea A/S", vat_number="DK12345678", country_code="DK")
            s.add(vendor)
            s.commit()
            s.add(Invoice(company_id=company_id, vendor_id=vendor.id, invoice_number="1",
                          currency="DKK", status="posted"))
        file_row = File(company_id=company_id, filename="Atea framework.pdf",
                        file_type="agreement_pdf", storage_path=KEY)
        s.add(file_row)
        s.commit()
        agreement = Agreement(company_id=company_id, file_id=file_row.id,
                              title="Atea framework", uploaded_by="user-1")
        s.add(agreement)
        s.commit()
        return agreement.id


def _read(engine, store, model):
    return read_pending(engine, store, model, limit=5, suggest_for=_no_suggestions)


def test_a_pending_agreement_is_read_into_review(engine, make_tenant, store, one_part):
    company_id = make_tenant()["company_id"]
    agreement_id = _pending(engine, company_id)

    assert _read(engine, store, Model()) == {"read": 1, "failed": 0}

    with Session(engine) as s:
        agreement = s.get(Agreement, agreement_id)
        assert (agreement.status, agreement.title) == ("review", "Framework agreement FA-2026-17")
        assert (agreement.reference, agreement.currency) == ("FA-2026-17", "DKK")
        assert agreement.supplier_vat_number == "DK12345678"
        assert agreement.vendor_id is not None
        terms = s.exec(select(AgreementTerm).order_by(AgreementTerm.kind)).all()
        assert [(term.kind, term.status, term.source) for term in terms] == [
            ("agreed_price", "draft", "ai"), ("preferred_supplier", "draft", "ai")]
        assert terms[0].quotes[0]["page"] == 3
        assert terms[0].scope_category_ids == ["category-1"]


def test_reading_again_keeps_confirmed_terms(engine, make_tenant, store, one_part):
    company_id = make_tenant()["company_id"]
    agreement_id = _pending(engine, company_id)
    _read(engine, store, Model())
    with Session(engine) as s:
        confirmed = s.exec(select(AgreementTerm).where(AgreementTerm.kind == "agreed_price")).one()
        confirmed.status = AgreementTermStatus.CONFIRMED.value
        confirmed.unit_price = 7950
        s.add(confirmed)
        agreement = s.get(Agreement, agreement_id)
        agreement.status = "pending"
        s.add(agreement)
        s.commit()

    _read(engine, store, Model())

    with Session(engine) as s:
        terms = s.exec(select(AgreementTerm)).all()
        assert len(terms) == 2
        price = next(term for term in terms if term.kind == "agreed_price")
        assert (price.status, price.unit_price) == ("confirmed", 7950)
        assert s.get(Agreement, agreement_id).status == "active"


def test_a_failed_read_is_retried_then_failed(engine, make_tenant, store, one_part, monkeypatch):
    monkeypatch.setattr(config, "AGREEMENT_MAX_ATTEMPTS", 2)
    company_id = make_tenant()["company_id"]
    agreement_id = _pending(engine, company_id, with_supplier=False)

    assert _read(engine, store, Model(fail=True)) == {"read": 0, "failed": 1}
    with Session(engine) as s:
        assert s.get(Agreement, agreement_id).status == "pending"

    _read(engine, store, Model(fail=True))
    with Session(engine) as s:
        agreement = s.get(Agreement, agreement_id)
        assert (agreement.status, agreement.read_attempts) == ("failed", 2)
        assert "could be read" in agreement.read_error


def test_a_missing_file_fails_the_read(engine, make_tenant, one_part):
    company_id = make_tenant()["company_id"]
    agreement_id = _pending(engine, company_id, with_supplier=False)

    _read(engine, MemoryFileStore(), Model())

    with Session(engine) as s:
        assert KEY in s.get(Agreement, agreement_id).read_error
