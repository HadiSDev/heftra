"""Stored items: what they bought in the last year, priced per pricing unit by their specification."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from agreement_books import Books
from ai_api.items.stored import refresh_company_items
from web_api.db.models import CompanyItem

TODAY = date(2026, 6, 1)
CABLE = {"item_class": "material", "product_type": "installation cable", "name": "Cat6 U/UTP",
         "pricing_unit": "m", "units_per_line_unit": 305, "confidence": 0.9}


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


def _refresh(session, books) -> None:
    refresh_company_items(session, books.company.id, today=TODAY, fx=Fx())


def _item(session) -> CompanyItem:
    (item,) = session.exec(select(CompanyItem)).all()
    return item


def _specify(session, spec: dict) -> None:
    item = _item(session)
    item.spec = spec
    session.add(item)
    session.commit()


def test_a_cable_box_is_priced_per_metre(session, books):
    books.line(books.proshop, "Cat6 U/UTP 305m kasse", quantity="4", unit_price="915", unit="stk")
    _refresh(session, books)
    _specify(session, CABLE)

    _refresh(session, books)

    item = _item(session)
    assert (item.quantity, item.unit_price) == (Decimal("1220"), Decimal("3"))
    assert item.unit_price_eur == Decimal("0.402")
    assert item.price_note is None
    assert item.spec == CABLE


def test_lines_without_a_quantity_give_no_price(session, books):
    books.line(books.proshop, "Cat6 U/UTP 305m kasse", quantity="0", unit_price="0",
               amount="915", unit="stk")
    _refresh(session, books)
    _specify(session, CABLE)

    _refresh(session, books)

    assert (_item(session).unit_price, _item(session).price_note) == (None, "no_quantity")


def test_an_item_without_a_specification_says_so(session, books):
    books.line(books.proshop, "Cat6 U/UTP 305m kasse", quantity="4", unit_price="915", unit="stk")

    _refresh(session, books)

    assert (_item(session).spend, _item(session).price_note) == (Decimal("3660"),
                                                                 "no_specification")


def test_the_line_unit_gives_the_pack_size_when_it_is_the_pricing_unit(session, books):
    books.line(books.atea, "Rundstål S235JR 20mm", quantity="250", unit_price="10.40", unit="kg")
    _refresh(session, books)
    _specify(session, {**CABLE, "pricing_unit": "kg", "units_per_line_unit": None})

    _refresh(session, books)

    assert (_item(session).quantity, _item(session).unit_price) == (Decimal("250"),
                                                                    Decimal("10.4"))


def test_an_item_not_bought_for_a_year_keeps_its_row_and_specification(session, books):
    books.line(books.proshop, "Cat6 U/UTP 305m kasse", quantity="4", unit_price="915", unit="stk")
    _refresh(session, books)
    _specify(session, CABLE)

    refresh_company_items(session, books.company.id, today=date(2027, 6, 1), fx=Fx())

    item = _item(session)
    assert (item.lines, item.spend, item.unit_price) == (0, Decimal("0"), None)
    assert (item.price_note, item.spec) == ("not_bought", CABLE)
