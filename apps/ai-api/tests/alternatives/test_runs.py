"""The alternatives runs: one item on request, and a company's scan of its largest spend."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from qdrant_client import QdrantClient
from sqlmodel import Session, select

from agreement_books import Books, embed
from ai_api import config
from ai_api.alternatives.run import ItemNotFound, find_alternatives, scan_alternatives
from ai_api.items.stored import refresh_company_items
from ai_api.specs.index import SpecIndex
from spec_stub import SpecModel, spec
from web_api.db.models import CompanyItem, ItemAlternative

TODAY = date(2026, 6, 1)
KEYBOARD = spec("Magic Keyboard", brand="Apple", part_number="MXK73DK/A")


class Fx:
    def get_rate(self, source, target, on):
        return (Decimal("0.134"), on)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def books(session) -> Books:
    return Books(session)


def _run_options(model):
    return {"ask": model, "embed_fn": embed, "fx": Fx(), "connectors": [], "today": TODAY,
            "index": SpecIndex(QdrantClient(location=":memory:"), embed)}


def _two_keyboards(books):
    books.line(books.atea, "Magic Keyboard (MXK73DK/A)", quantity="4", unit_price="1136",
               unit="stk")
    books.line(books.proshop, "Apple Magic Keyboard MXK73DK/A", quantity="2", unit_price="999",
               unit="stk")


def test_one_item_is_searched_after_its_specification_is_read(session, books):
    _two_keyboards(books)
    refresh_company_items(session, books.company.id, today=TODAY, fx=Fx())
    model = SpecModel({"Keyboard": KEYBOARD})
    find_alternatives(session, books.company.id,
                      session.exec(select(CompanyItem).where(
                          CompanyItem.item_name.contains("Apple"))).one().id,
                      **_run_options(model))
    atea = session.exec(select(CompanyItem).where(
        CompanyItem.vendor_id == books.atea.id)).one()

    summary = find_alternatives(session, books.company.id, atea.id, **_run_options(model))

    (alternative,) = session.exec(select(ItemAlternative)).all()
    assert (alternative.item_id, alternative.unit_price) == (atea.id, Decimal("999"))
    assert summary["history_alternatives"] == 1


def test_an_item_of_another_company_is_refused(session, books):
    with pytest.raises(ItemNotFound):
        find_alternatives(session, books.company.id, "no-such-item",
                          **_run_options(SpecModel({})))


def test_a_scan_searches_the_largest_spend_up_to_the_limit(session, books, monkeypatch):
    monkeypatch.setattr(config, "ALTERNATIVES_SCAN_ITEMS", 1)
    _two_keyboards(books)

    summary = scan_alternatives(session, books.company.id, **_run_options(
        SpecModel({"Keyboard": KEYBOARD})))

    searched = session.exec(select(CompanyItem).where(
        CompanyItem.searched_at.is_not(None))).all()
    assert [item.vendor_id for item in searched] == [books.atea.id]
    assert (summary["items"], summary["searched"]) == (2, 1)
    assert summary["history_alternatives"] == 1


def test_a_recent_search_is_not_repeated(session, books):
    _two_keyboards(books)
    options = _run_options(SpecModel({"Keyboard": KEYBOARD}))
    scan_alternatives(session, books.company.id, **options)

    summary = scan_alternatives(session, books.company.id, **options)

    assert summary["searched"] == 0
