"""The open web: SearXNG first, DuckDuckGo when it fails, and only readable shop pages."""
from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from ai_api.marketplaces.market import market_for
from ai_api.marketplaces.pages.page import Page
from ai_api.marketplaces.pages.reader import PageReader
from ai_api.marketplaces.source import ConnectorFailed
from ai_api.marketplaces.web.connector import WebSearch
from ai_api.marketplaces.web.search import SearchFailed, SearchResult, SearxngSearch

DK = market_for("DK")
PRODUCT = """<script type="application/ld+json">{"@type": "Product", "name": "Cat6 U/UTP 305m",
"offers": {"price": "1249.00", "priceCurrency": "DKK",
"priceSpecification": {"valueAddedTaxIncluded": true}}}</script>"""


class Results:
    def __init__(self, urls: list[str], *, name: str = "stub", fails: bool = False) -> None:
        self.name = name
        self.urls = urls
        self.fails = fails

    def results(self, query, market, limit):
        if self.fails:
            raise SearchFailed(f"{self.name} is down")
        return [SearchResult(url, "") for url in self.urls][:limit]


class Web:
    def __init__(self) -> None:
        self.fetched: list[str] = []

    def __call__(self, urls: list[str]) -> list[Page]:
        self.fetched += urls
        return [Page(url, PRODUCT, "Cat6 cable") for url in urls]


class Never:
    def __call__(self, prompt: str) -> str:
        raise AssertionError("the LLM was asked")


def test_searxng_is_asked_for_json_in_the_markets_language():
    seen = {}

    def answer(request: httpx.Request) -> httpx.Response:
        seen.update(request.url.params)
        return httpx.Response(200, json={"results": [{"url": "https://shop.dk/p/1",
                                                      "title": "Cat6"}]})

    client = httpx.Client(transport=httpx.MockTransport(answer))
    found = SearxngSearch("http://localhost:8888/", client).results("cat6 305m", DK, 5)

    assert [result.url for result in found] == ["https://shop.dk/p/1"]
    assert (seen["format"], seen["language"]) == ("json", "da-DK")


def test_a_searxng_error_is_a_failure():
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500)))
    with pytest.raises(SearchFailed):
        SearxngSearch("http://localhost:8888", client).results("cat6", DK, 5)


def test_pages_found_are_read_and_blocked_hosts_skipped():
    web = Web()
    connector = WebSearch([Results(["https://www.pricerunner.dk/x", "https://shop.dk/manual.pdf",
                                    "https://www.shop.dk/p/1"])], web, PageReader(Never()))

    (offer,) = connector.search("cat6", DK)

    assert web.fetched == ["https://www.shop.dk/p/1"]
    assert (offer.seller, offer.seller_country, offer.price, offer.vat_included) == \
        ("shop.dk", "DK", Decimal("1249.00"), True)


def test_duckduckgo_is_the_fallback():
    web = Web()
    connector = WebSearch([Results([], name="searxng", fails=True),
                           Results(["https://shop.dk/p/2"], name="duckduckgo")], web,
                          PageReader(Never()))

    connector.search("cat6", DK)

    assert web.fetched == ["https://shop.dk/p/2"]


def test_no_search_answering_is_the_connectors_failure():
    connector = WebSearch([Results([], fails=True)], Web(), PageReader(Never()))
    with pytest.raises(ConnectorFailed):
        connector.search("cat6", DK)
