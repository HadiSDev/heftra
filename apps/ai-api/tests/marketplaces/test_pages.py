"""Product pages read from their structured data, and by the LLM where it falls short."""
from __future__ import annotations

import json
from decimal import Decimal

from ai_api.marketplaces.pages.page import Page
from ai_api.marketplaces.pages.prices import parse_price
from ai_api.marketplaces.pages.reader import PageReader
from ai_api.marketplaces.pages.structured import structured_products

JSON_LD = """<html><head><script type="application/ld+json">
{"@context": "https://schema.org", "@graph": [{"@type": "BreadcrumbList"},
 {"@type": ["Product"], "name": "Lenovo ThinkPad T14 Gen 5 21ML003XMX",
  "gtin13": "0197529000000", "mpn": "21ML003XMX", "brand": {"@type": "Brand", "name": "Lenovo"},
  "offers": {"@type": "Offer", "price": "10500.00", "priceCurrency": "DKK",
             "availability": "https://schema.org/InStock"}}]}
</script></head><body>ThinkPad</body></html>"""

MICRODATA = """<div itemscope itemtype="https://schema.org/Product">
<h1 itemprop="name">Lotus toiletpapir 8 ruller</h1>
<div itemprop="offers" itemscope itemtype="https://schema.org/Offer">
<meta itemprop="priceCurrency" content="DKK"><span itemprop="price" content="100,00">100,00 kr.</span>
</div></div>"""


class Never:
    def __call__(self, prompt: str) -> str:
        raise AssertionError("the LLM was asked")


class Reads:
    def __init__(self, offers: list[dict]) -> None:
        self.offers = offers
        self.prompts = 0

    def __call__(self, prompt: str) -> str:
        self.prompts += 1
        return json.dumps({"offers": self.offers})


def _page(html: str, markdown: str = "Product text") -> Page:
    return Page(url="https://shop.dk/p/1", html=html, markdown=markdown)


def test_json_ld_in_a_graph_is_read():
    (product,) = structured_products(JSON_LD)
    assert (product.price, product.currency, product.part_number, product.brand,
            product.availability) == (Decimal("10500.00"), "DKK", "21ML003XMX", "Lenovo",
                                      "InStock")


def test_microdata_is_read():
    (product,) = structured_products(MICRODATA)
    assert (product.name, product.price) == ("Lotus toiletpapir 8 ruller", Decimal("100.00"))


def test_a_page_with_structured_data_needs_no_llm_when_the_shop_says_how_vat_is_shown():
    (offer,) = PageReader(Never()).offers(_page(JSON_LD), seller="Shop", seller_country="DK",
                                          vat_included=True)
    assert (offer.price, offer.vat_included, offer.part_number) == (Decimal("10500.00"), True,
                                                                    "21ML003XMX")


def test_the_llm_says_whether_vat_is_included_when_nothing_else_does():
    reads = Reads([{"title": "ThinkPad", "price": "10.500,00", "currency": "DKK",
                    "vat_included": False}])
    (offer,) = PageReader(reads).offers(_page(JSON_LD), seller="Shop", seller_country="DK",
                                        vat_included=None)
    assert (offer.price, offer.vat_included) == (Decimal("10500.00"), False)


def test_a_page_without_structured_data_is_read_by_the_llm():
    reads = Reads([{"title": "Cat6 U/UTP 305m", "price": "1.249,00 kr.", "currency": "DKK",
                    "vat_included": True, "pack": "305 m"}])
    (offer,) = PageReader(reads).offers(_page("<html>no data</html>"), seller="Shop",
                                        seller_country="DK", vat_included=None)
    assert (offer.price, offer.pack, offer.vat_included) == (Decimal("1249.00"), "305 m", True)


def test_an_offer_without_a_price_or_vat_is_dropped():
    reads = Reads([{"title": "Cat6", "price": "", "currency": "DKK", "vat_included": True},
                   {"title": "Cat6", "price": "100", "currency": "DKK", "vat_included": None}])
    assert PageReader(reads).offers(_page("<html></html>"), seller="Shop", seller_country="DK",
                                    vat_included=None) == []


def test_prices_as_shops_write_them():
    assert parse_price("1.249,00 kr.") == Decimal("1249.00")
    assert parse_price("DKK 1 249,-") == Decimal("1249")
    assert parse_price("kr. 499,95") == Decimal("499.95")
    assert parse_price(1249) == Decimal("1249")
    assert parse_price("ring for pris") is None
