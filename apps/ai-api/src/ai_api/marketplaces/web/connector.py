"""The open-web connector: the search's product pages, read into offers."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from ... import config
from ..market import Market
from ..offer import Offer
from ..pages.page import Fetch
from ..pages.reader import PageReader
from ..source import ConnectorFailed
from .search import SearchFailed, SearchProvider

logger = logging.getLogger("ai_api.marketplaces")

BLOCKED_HOSTS = frozenset({
    "amazon.com", "amazon.de", "amazon.co.uk", "amazon.se", "ebay.com", "ebay.de",
    "facebook.com", "instagram.com", "linkedin.com", "youtube.com", "x.com", "twitter.com",
    "reddit.com", "wikipedia.org", "trustpilot.com", "proff.dk", "cvr.dk", "krak.dk",
    "pricerunner.dk", "pricerunner.com", "pricespy.co.uk", "prisjagt.dk", "prisjakt.nu",
    "idealo.de", "kelkoo.com", "manualslib.com", "manua.ls", "manualzz.com",
})
NOT_PAGES = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")
COUNTRY_TLDS = {"dk": "DK", "se": "SE", "no": "NO", "fi": "FI", "de": "DE", "nl": "NL",
                "uk": "GB"}


class WebSearch:
    name = "web"

    def __init__(self, providers: list[SearchProvider], fetch: Fetch, reader: PageReader) -> None:
        self._providers = providers
        self._fetch = fetch
        self._reader = reader

    def enabled(self) -> bool:
        return config.ALTERNATIVES_WEB_ENABLED and bool(self._providers)

    def search(self, query: str, market: Market) -> list[Offer]:
        """The first product pages the search finds for the query, read into offers."""
        wanted = config.ALTERNATIVES_PAGES_PER_ITEM
        urls = [url for url in self._urls(query, market, wanted * 3) if _readable(url)][:wanted]
        offers: list[Offer] = []
        for page in self._fetch(urls):
            host = urlparse(page.url).hostname or ""
            offers += self._reader.offers(page, seller=_seller(host),
                                          seller_country=_country(host, market),
                                          vat_included=None)
        return offers

    def _urls(self, query: str, market: Market, limit: int) -> list[str]:
        errors: list[str] = []
        for provider in self._providers:
            try:
                return [result.url for result in provider.results(query, market, limit)]
            except SearchFailed as error:
                logger.warning("marketplaces: %s failed, trying the next search: %s",
                               provider.name, error)
                errors.append(str(error))
        raise ConnectorFailed("; ".join(errors) or "no search configured")


def _readable(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")
    if parsed.scheme not in ("http", "https") or parsed.path.lower().endswith(NOT_PAGES):
        return False
    return not any(host == blocked or host.endswith(f".{blocked}") for blocked in BLOCKED_HOSTS)


def _seller(host: str) -> str:
    return host.lower().removeprefix("www.")


def _country(host: str, market: Market) -> str:
    return COUNTRY_TLDS.get(host.rsplit(".", 1)[-1].lower(), market.country)
