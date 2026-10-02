"""Shops searched through their own site search, their first product page read."""
from __future__ import annotations

from decimal import Decimal

import pytest

from ai_api import config
from ai_api.marketplaces.market import market_for
from ai_api.marketplaces.pages.page import Page
from ai_api.marketplaces.pages.reader import PageReader
from ai_api.marketplaces.shops.catalog import shops_in
from ai_api.marketplaces.shops.connector import ShopSearch

SHOPS = """shops:
  - name: Proshop
    market: DK
    search_url: https://www.proshop.dk/?s={query}
    product_link: ^https://www\\.proshop\\.dk/[^/?#]+/[^/?#]+/\\d{5,}$
    prices_include_vat: true
  - name: Generic
    market: DK
    search_url: https://generic.dk/search?q={query}
    prices_include_vat: null
  - name: Svensk
    market: SE
    search_url: https://shop.se/s?q={query}
"""

PRODUCT = """<script type="application/ld+json">{"@type": "Product", "name": "ThinkPad T14",
"mpn": "21ML003XMX", "offers": {"price": "10500", "priceCurrency": "DKK"}}</script>"""


class Web:
    def __init__(self, pages: dict[str, Page]) -> None:
        self.pages = pages
        self.fetched: list[str] = []

    def __call__(self, urls: list[str]) -> list[Page]:
        self.fetched += urls
        return [self.pages[url] for url in urls if url in self.pages]


class Never:
    def __call__(self, prompt: str) -> str:
        raise AssertionError("the LLM was asked")


@pytest.fixture
def shops_file(tmp_path, monkeypatch):
    path = tmp_path / "shops.yaml"
    path.write_text(SHOPS)
    monkeypatch.setattr(config, "ALTERNATIVES_SHOPS_FILE", str(path))
    return path


def test_the_bundled_list_loads():
    assert {shop.name for shop in shops_in("DK")} >= {"Proshop", "Komplett"}


def test_only_the_markets_shops_are_searched(shops_file):
    assert [shop.name for shop in shops_in("DK")] == ["Proshop", "Generic"]


def test_each_shops_first_product_is_read(shops_file):
    product = "https://www.proshop.dk/Baerbar/Lenovo-ThinkPad-T14/3243478"
    web = Web({
        "https://www.proshop.dk/?s=21ML003XMX": Page(
            "https://www.proshop.dk/?s=21ML003XMX", "", "",
            links=("https://www.proshop.dk/Baerbar", product)),
        "https://generic.dk/search?q=21ML003XMX": Page(
            "https://generic.dk/search?q=21ML003XMX", "", "", links=("https://generic.dk/om-os",)),
        product: Page(product, PRODUCT, "ThinkPad T14 Gen 5"),
    })

    (offer,) = ShopSearch(web, PageReader(Never())).search("21ML003XMX", market_for("DK"))

    assert (offer.seller, offer.url, offer.price, offer.vat_included, offer.seller_country) == \
        ("Proshop", product, Decimal("10500"), True, "DK")
    assert "https://www.proshop.dk/Baerbar" not in web.fetched


def test_a_shop_without_a_pattern_takes_product_like_links(shops_file):
    (generic,) = [shop for shop in shops_in("DK") if shop.name == "Generic"]
    assert generic.is_product("https://generic.dk/product/cat6-kabel")
    assert generic.is_product("https://generic.dk/kabler/cat6-305m-123456")
    assert not generic.is_product("https://generic.dk/om-os")
    assert not generic.is_product("https://other.dk/product/1")
