"""One item's search: alternatives stored with their saving, reviews kept, dismissals held."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from ai_api.alternatives.search import SearchTools, search_item
from ai_api.marketplaces.offer import Offer
from ai_api.specs.reader import SpecReader
from alternatives_books import Shelves
from spec_stub import SpecModel, spec
from web_api.db.models import Company, ItemAlternative, Organization, Product

CABLE = {"item_class": "material", "product_type": "network installation cable",
         "pricing_unit": "m", "units_per_line_unit": 305}


class Fx:
    def get_rate(self, source, target, on):
        return (Decimal("0.134"), on) if target == "EUR" else (Decimal("7.46"), on)


class Shop:
    name = "shop"

    def __init__(self, offers: list[Offer]) -> None:
        self.offers = offers
        self.asked = 0

    def enabled(self):
        return True

    def search(self, query, market):
        self.asked += 1
        return self.offers


def never(prompt: str) -> str:
    raise AssertionError("the LLM was asked")


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def shelves(session) -> Shelves:
    return Shelves(session)


def _tools(connectors=(), answers=None) -> SearchTools:
    return SearchTools(ask=never, reader=SpecReader(SpecModel(answers or {})), index=None,
                       connectors=list(connectors), fx=Fx(), today=date(2026, 6, 1))


def _keyboards(shelves):
    acme = shelves.organization("Acme")
    keyboard = shelves.product("MXK73DK/A")
    company = shelves.company(acme, "Acme DK")
    company.country_code = "DK"
    shelves.session.add(company)
    mine = shelves.item(company, "Magic Keyboard", unit_price="1136", quantity="10",
                        product=keyboard, vendor=shelves.vendor("CS-Online"))
    cheaper = shelves.item(shelves.company(acme, "Acme SE"), "Magic Keyboard", unit_price="999",
                           product=keyboard, vendor=shelves.vendor("Proshop"))
    return mine, cheaper


def _alternatives(session) -> list[ItemAlternative]:
    return list(session.exec(select(ItemAlternative)).all())


def test_an_exact_alternative_is_stored_with_its_yearly_saving(session, shelves):
    mine, cheaper = _keyboards(shelves)

    counts = search_item(session, mine, _tools())

    (alternative,) = _alternatives(session)
    assert (alternative.source, alternative.match, alternative.unit_price) == \
        ("history", "exact", Decimal("999"))
    assert (alternative.saving_yearly, alternative.saving_percent) == (Decimal("1370.00"),
                                                                       Decimal("12.06"))
    assert alternative.origin["supplier"] == "Proshop"
    assert counts["history_alternatives"] == 1
    assert mine.searched_at is not None


def test_a_dismissed_alternative_is_not_raised_again(session, shelves):
    mine, _ = _keyboards(shelves)
    search_item(session, mine, _tools())
    (alternative,) = _alternatives(session)
    alternative.review_status = "dismissed"
    alternative.dismiss_reason = "supplier_not_approved"
    session.add(alternative)
    session.commit()

    search_item(session, mine, _tools())

    (kept,) = _alternatives(session)
    assert kept.review_status == "dismissed"


def test_an_open_alternative_not_found_again_goes(session, shelves):
    mine, cheaper = _keyboards(shelves)
    search_item(session, mine, _tools())
    cheaper.unit_price = Decimal("1200")
    session.add(cheaper)
    session.commit()

    search_item(session, mine, _tools())

    assert _alternatives(session) == []


def test_a_marketplace_offer_becomes_an_alternative(session, shelves):
    acme = shelves.organization("Acme")
    company = shelves.company(acme)
    company.country_code = "DK"
    session.add(company)
    item = shelves.item(company, "Cat6 U/UTP 305m", unit_price="3.00", quantity="1220",
                        fields=CABLE)
    shop = Shop([Offer("Shop", "Cat6 U/UTP 305m", "https://shop.dk/p/1", Decimal("700"), "DKK",
                       False, pack="305 m")])

    search_item(session, item, _tools([shop], {"Cat6": spec("Cat6 U/UTP", **CABLE)}))

    (alternative,) = _alternatives(session)
    assert (alternative.source, alternative.match) == ("marketplace", "equivalent")
    assert alternative.origin["url"] == "https://shop.dk/p/1"
    assert alternative.saving_yearly == Decimal("860.00")


def test_an_unsure_specification_is_not_searched_on_marketplaces(session, shelves):
    company = shelves.company(shelves.organization("Acme"))
    company.country_code = "DK"
    session.add(company)
    item = shelves.item(company, "Cat6 U/UTP 305m", unit_price="3.00",
                        fields={**CABLE, "confidence": 0.2})
    shop = Shop([])

    search_item(session, item, _tools([shop]))

    assert shop.asked == 0


def test_an_item_without_a_price_is_searched_for_nothing(session, shelves):
    company = shelves.company(shelves.organization("Acme"))
    item = shelves.item(company, "Cat6", unit_price="3.00", fields=CABLE)
    item.unit_price = None
    session.add(item)
    session.commit()

    counts = search_item(session, item, _tools())

    assert counts["unpriced"] == 1



def test_a_product_ruled_not_equivalent_is_not_proposed_again(session, shelves):
    mine, cheaper = _keyboards(shelves)
    search_item(session, mine, _tools())
    (alternative,) = _alternatives(session)
    alternative.review_status = "dismissed"
    alternative.dismiss_reason = "not_equivalent"
    session.add(alternative)
    acme = session.get(Company, mine.company_id).organization_id
    norway = shelves.company(session.get(Organization, acme), "Acme NO")
    shelves.item(norway, "Magic Keyboard", unit_price="950",
                 product=session.get(Product, mine.product_id))

    search_item(session, mine, _tools())

    assert [entry.review_status for entry in _alternatives(session)] == ["dismissed"]
