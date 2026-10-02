"""Distributors' APIs read into offers with their price breaks, without VAT."""
from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from ai_api.marketplaces.distributors.digikey import DigiKey
from ai_api.marketplaces.distributors.farnell import Farnell
from ai_api.marketplaces.distributors.mouser import Mouser
from ai_api.marketplaces.market import market_for
from ai_api.marketplaces.source import ConnectorFailed

DK = market_for("DK")


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_mouser_parts_with_localised_prices():
    def answer(request: httpx.Request) -> httpx.Response:
        assert request.url.params["apiKey"] == "key"
        return httpx.Response(200, json={"Errors": [], "SearchResults": {"NumberOfResult": 1, "Parts": [
            {"ManufacturerPartNumber": "B0606", "Manufacturer": "Bourns",
             "Description": "Cat6 patch cable 2m", "ProductDetailUrl": "https://www.mouser.dk/p/1",
             "Availability": "120 In Stock",
             "PriceBreaks": [{"Quantity": 10, "Price": "21,50 kr", "Currency": "DKK"},
                             {"Quantity": 1, "Price": "25,00 kr", "Currency": "DKK"}]}]}})

    (offer,) = Mouser("key", _client(answer)).search("cat6 patch", DK)

    assert (offer.price, offer.currency, offer.vat_included) == (Decimal("25.00"), "DKK", False)
    assert [entry.quantity for entry in offer.price_breaks] == [1, 10]


def test_mouser_errors_are_the_connectors_failure():
    client = _client(lambda request: httpx.Response(200, json={"Errors": [{"Message": "Bad key"}]}))
    with pytest.raises(ConnectorFailed):
        Mouser("key", client).search("cat6", DK)


def test_digikey_gets_a_token_once_and_prices_in_the_markets_currency():
    calls = {"token": 0}

    def answer(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            calls["token"] += 1
            return httpx.Response(200, json={"access_token": "t", "expires_in": 600})
        assert request.headers["X-DIGIKEY-Locale-Currency"] == "DKK"
        assert request.headers["Authorization"] == "Bearer t"
        return httpx.Response(200, json={"Products": [
            {"ManufacturerProductNumber": "RJ45-8P8C", "Manufacturer": {"Name": "Amphenol"},
             "Description": {"ProductDescription": "Modular plug RJ45",
                             "DetailedDescription": "8P8C Cat6"},
             "ProductUrl": "https://www.digikey.dk/p/2", "QuantityAvailable": 5000,
             "ProductVariations": [{"StandardPricing": [
                 {"BreakQuantity": 1, "UnitPrice": 4.12}, {"BreakQuantity": 100, "UnitPrice": 2.9}]}]}]})

    digikey = DigiKey("id", "secret", _client(answer))
    digikey.search("rj45", DK)
    (offer,) = digikey.search("rj45 cat6", DK)

    assert calls["token"] == 1
    assert (offer.price, offer.currency, offer.brand) == (Decimal("4.12"), "DKK", "Amphenol")
    assert offer.price_breaks[-1] == offer.price_breaks[1]


def test_farnell_uses_the_markets_store_and_its_pack_size():
    def answer(request: httpx.Request) -> httpx.Response:
        assert request.url.params["storeInfo.id"] == "dk.farnell.com"
        assert request.url.params["term"] == "any:cat6 305m"
        return httpx.Response(200, json={"keywordSearchReturn": {"products": [
            {"sku": "2421201", "displayName": "Cat6 U/UTP cable, 305m", "brandName": "Pro Signal",
             "translatedManufacturerPartNumber": "PSG91", "packSize": 1, "unitOfMeasure": "REEL",
             "prices": [{"from": 1, "to": 2, "cost": 1180.5}, {"from": 3, "to": 9, "cost": 990}],
             "stock": {"level": 12}}]}})

    (offer,) = Farnell("key", _client(answer)).search("cat6 305m", DK)

    assert (offer.url, offer.price, offer.part_number) == ("https://dk.farnell.com/dp/2421201",
                                                           Decimal("1180.5"), "PSG91")
    assert offer.price_breaks[1].price == Decimal("990")


def test_a_distributor_without_a_key_is_not_used():
    assert not Mouser("").enabled()
    assert not DigiKey("", "").enabled()
    assert not Farnell("").enabled()
