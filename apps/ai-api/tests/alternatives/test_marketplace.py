"""Offers from marketplace connectors: cached and shared, priced at the order quantity, and a
failing connector skipped."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, select

from ai_api.alternatives.sources.marketplace import ConnectorHealth, marketplace_candidates
from ai_api.marketplaces.cache import cached_offers
from ai_api.marketplaces.market import market_for
from ai_api.marketplaces.offer import Offer, PriceBreak
from ai_api.marketplaces.source import ConnectorFailed
from ai_api.specs.reader import SpecReader
from alternatives_books import Shelves
from spec_stub import SpecModel, spec
from web_api.db.models import MarketplaceQuery

DK = market_for("DK")
CABLE = {"item_class": "material", "product_type": "network installation cable",
         "pricing_unit": "m", "units_per_line_unit": 305}


class Shop:
    def __init__(self, offers: list[Offer], *, name: str = "shop", fails: bool = False) -> None:
        self.name = name
        self.offers = offers
        self.fails = fails
        self.asked = 0

    def enabled(self) -> bool:
        return True

    def search(self, query, market):
        self.asked += 1
        if self.fails:
            raise ConnectorFailed("503 from the shop")
        return self.offers


def same_currency(amount, currency, on):
    return amount


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def shelves(session) -> Shelves:
    return Shelves(session)


def _cable_item(shelves):
    item = shelves.item(shelves.company(shelves.organization("Acme")), "Cat6 U/UTP 305m",
                        unit_price="3.00", quantity="1220", fields=CABLE)
    item.order_quantity = Decimal("4")
    shelves.session.add(item)
    shelves.session.commit()
    return item


def test_an_answer_is_reused_within_its_ttl(session):
    shop = Shop([Offer("Shop", "Cat6", "https://shop.dk/p/1", Decimal("700"), "DKK", True)])

    cached_offers(session, shop, "cat6", DK)
    again = cached_offers(session, shop, "cat6", DK)

    assert shop.asked == 1
    assert [offer.url for offer in again] == ["https://shop.dk/p/1"]


def test_a_cable_from_a_distributor_at_the_order_quantity(session, shelves):
    item = _cable_item(shelves)
    distributor = Shop([Offer("Distributor", "Cat6 U/UTP 305m box", "https://dist.com/p/9",
                              Decimal("900"), "DKK", False, pack="305 m",
                              price_breaks=(PriceBreak(1, Decimal("900")),
                                            PriceBreak(3, Decimal("700"))))])
    model = SpecModel({"Cat6": spec("Cat6 U/UTP", **CABLE)})

    (found,) = marketplace_candidates(session, shelves.context(item), DK, [distributor],
                                      SpecReader(model), ConnectorHealth(), same_currency)

    assert found.unit_price == Decimal("2.295082")
    assert found.origin["seller"] == "Distributor"


def test_a_danish_shop_price_includes_vat(session, shelves):
    item = _cable_item(shelves)
    shop = Shop([Offer("Shop", "Cat6 U/UTP 305m", "https://shop.dk/p/1", Decimal("1000"), "DKK",
                       True, pack="305 m")])
    model = SpecModel({"Cat6": spec("Cat6 U/UTP", **CABLE)})

    (found,) = marketplace_candidates(session, shelves.context(item), DK, [shop],
                                      SpecReader(model), ConnectorHealth(), same_currency)

    assert found.unit_price == Decimal("2.622951")


def test_a_failing_connector_is_skipped_and_the_others_still_answer(session, shelves):
    item = _cable_item(shelves)
    broken = Shop([], name="broken", fails=True)
    working = Shop([Offer("Shop", "Cat6 U/UTP 305m", "https://shop.dk/p/1", Decimal("700"),
                          "DKK", False, pack="305 m")])
    health = ConnectorHealth()

    found = marketplace_candidates(session, shelves.context(item), DK, [broken, working],
                                   SpecReader(SpecModel({"Cat6": spec("Cat6", **CABLE)})),
                                   health, same_currency)

    assert broken.asked == 1
    assert "503" in health.failed["broken"]
    assert len(found) == 1
    assert session.exec(select(MarketplaceQuery).where(
        MarketplaceQuery.connector == "broken")).first() is None


def test_an_offer_whose_pack_size_cant_be_told_is_dropped(session, shelves):
    item = _cable_item(shelves)
    shop = Shop([Offer("Shop", "Cat6 cable", "https://shop.dk/p/2", Decimal("100"), "DKK", True)])
    unknown_pack = spec("Cat6", **{**CABLE, "units_per_line_unit": None})

    found = marketplace_candidates(session, shelves.context(item), DK, [shop],
                                   SpecReader(SpecModel({"Cat6": unknown_pack})),
                                   ConnectorHealth(), same_currency)

    assert found == []


def test_no_market_no_offers(session, shelves):
    item = _cable_item(shelves)
    assert marketplace_candidates(session, shelves.context(item), None, [Shop([])],
                                  SpecReader(SpecModel({})), ConnectorHealth(),
                                  same_currency) == []
