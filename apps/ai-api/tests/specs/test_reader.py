"""Reading specifications in batches, and what is done with them."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from agreement_books import Books
from ai_api.items.stored import refresh_company_items
from ai_api.specs.prompt import ItemText
from ai_api.specs.reader import SpecReader
from ai_api.specs.refresh import due_for_spec, specify_items
from spec_stub import SpecModel, spec
from web_api.db.models import CompanyItem, Product

TODAY = date(2026, 6, 1)
LAPTOP = spec("ThinkPad T14 Gen 5", brand="Lenovo", part_number="21ML-003XMX",
              attributes=[{"name": "Memory", "kind": "numeric", "value": "16 GB", "number": 16,
                           "unit": "GB", "direction": "more"},
                          {"name": "processor", "kind": "tiered", "value": "Core Ultra 7 155U",
                           "family": "Intel Core Ultra", "tier": "7", "generation": 1}])
CABLE = spec("Cat6 U/UTP", item_class="material", product_type="network installation cable",
             pricing_unit="m", units_per_line_unit=305)


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


def _text(name: str) -> ItemText:
    return ItemText(item_name=name, description=None, unit="stk", category=None, supplier=None)


def test_a_batch_is_one_prompt():
    model = SpecModel({"ThinkPad": LAPTOP, "Cat6": CABLE})
    read = SpecReader(model, batch=8).read({"a": _text("ThinkPad T14"), "b": _text("Cat6 305m")})

    assert model.prompts == 1
    assert read["a"].attributes[0].name == "memory"
    assert (read["b"].pricing_unit.value, read["b"].units_per_line_unit) == ("m", 305)


def test_an_unreadable_batch_is_read_one_by_one():
    model = SpecModel({"ThinkPad": LAPTOP, "Cat6": CABLE}, fail_batches=True)
    read = SpecReader(model, batch=8).read({"a": _text("ThinkPad T14"), "b": _text("Cat6 305m")})

    assert model.prompts == 3
    assert set(read) == {"a", "b"}


def test_read_specifications_are_stored_linked_and_priced(session, books):
    books.line(books.proshop, "Cat6 U/UTP 305m kasse", quantity="4", unit_price="915", unit="stk")
    books.line(books.atea, "Lenovo ThinkPad T14 Gen 5", quantity="2", unit_price="9200",
               unit="stk")
    refresh_company_items(session, books.company.id, today=TODAY, fx=Fx())

    counts = specify_items(session, due_for_spec(session, books.company.id),
                           SpecReader(SpecModel({"ThinkPad": LAPTOP, "Cat6": CABLE})),
                           Decimal("0.134"))

    assert (counts.read, counts.failed) == (2, 0)
    cable = session.exec(select(CompanyItem).where(CompanyItem.item_name.contains("Cat6"))).one()
    assert (cable.unit_price, cable.spec_source) == (Decimal("3"), "ai")
    assert cable.product_id is None
    (product,) = session.exec(select(Product)).all()
    assert (product.part_number, product.brand) == ("21ML003XMX", "lenovo")
    assert due_for_spec(session, books.company.id) == []


def test_an_item_that_cant_be_read_is_tried_again_later(session, books):
    books.line(books.proshop, "Mystery part", quantity="1", unit_price="10", unit="stk")
    refresh_company_items(session, books.company.id, today=TODAY, fx=Fx())

    counts = specify_items(session, due_for_spec(session, books.company.id),
                           SpecReader(SpecModel({})), None)

    assert counts.failed == 1
    (item,) = due_for_spec(session, books.company.id)
    assert item.spec_failures == 1


def test_a_persons_specification_is_never_read_again(session, books):
    books.line(books.proshop, "Cat6 U/UTP 305m kasse", quantity="4", unit_price="915", unit="stk")
    refresh_company_items(session, books.company.id, today=TODAY, fx=Fx())
    (item,) = session.exec(select(CompanyItem)).all()
    item.spec = CABLE
    item.spec_source = "human"
    session.add(item)
    session.commit()

    assert due_for_spec(session, books.company.id) == []


def test_one_keyboard_from_two_suppliers_is_one_product(session, books):
    keyboard = spec("Magic Keyboard", brand="Apple", part_number="MXK73DK/A")
    books.line(books.atea, "Magic Keyboard Touch Id Num Key (MXK73DK/A)", quantity="1",
               unit_price="1136", unit="stk")
    books.line(books.proshop, "Apple Magic Keyboard med Touch ID MXK73DK/A", quantity="1",
               unit_price="999", unit="stk")
    refresh_company_items(session, books.company.id, today=TODAY, fx=Fx())

    specify_items(session, due_for_spec(session, books.company.id),
                  SpecReader(SpecModel({"Keyboard": {**keyboard, "brand": "Apple"},
                                        "Magic Keyboard": keyboard})), None)

    items = session.exec(select(CompanyItem)).all()
    assert len({item.product_id for item in items}) == 1
    assert items[0].product_id is not None
