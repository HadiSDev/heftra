"""Alternatives say what switching would break under the company's agreements."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from agreement_books import Books
from ai_api.alternatives.agreements import agreement_notes, item_bindings
from ai_api.alternatives.sources.found import Found
from ai_api.compliance.keys import term_key
from web_api.company_context import business_context
from web_api.db.models import (
    AgreementScopeJudgement,
    AgreementTermKind,
    AlternativeSource,
    CompanyItem,
)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def books(session) -> Books:
    return Books(session)


def _item_under_a_preferred_supplier_term(session, books) -> CompanyItem:
    agreement = books.agreement()
    term = books.term(agreement, AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    item = CompanyItem(company_id=books.company.id, item_key="laptop-key", item_name="Laptop",
                       lines=1)
    session.add(item)
    session.add(AgreementScopeJudgement(
        term_id=term.id, term_key=term_key(term, business_context(books.company)),
        question_key="laptop-key", in_scope=True, reason="A laptop."))
    books.atea.website = "https://www.atea.dk"
    session.add(books.atea)
    session.commit()
    return item


def _found(**fields) -> Found:
    return Found(source=AlternativeSource.HISTORY, ref_key="x", name="Laptop",
                 unit_price=Decimal("8000"), origin={}, **fields)


def test_another_supplier_under_a_preferred_supplier_term_is_off_contract(session, books):
    item = _item_under_a_preferred_supplier_term(session, books)
    bindings = item_bindings(session, books.company, item, date(2026, 6, 1))

    (note,) = agreement_notes(_found(vendor_id=books.proshop.id), bindings)

    assert note["kind"] == "off_contract"
    assert "Atea A/S" in note["text"]


def test_the_agreements_own_supplier_breaks_nothing(session, books):
    item = _item_under_a_preferred_supplier_term(session, books)
    bindings = item_bindings(session, books.company, item, date(2026, 6, 1))

    assert agreement_notes(_found(vendor_id=books.atea.id), bindings) == []
    assert agreement_notes(_found(seller_host="atea.dk"), bindings) == []
    assert agreement_notes(_found(seller_host="proshop.dk"), bindings) != []


def test_an_item_out_of_scope_is_bound_by_nothing(session, books):
    books.term(books.agreement(), AgreementTermKind.PREFERRED_SUPPLIER, "Laptops")
    item = CompanyItem(company_id=books.company.id, item_key="coffee", lines=1)

    assert item_bindings(session, books.company, item, date(2026, 6, 1)) == []
