"""Web search for product pages: a self-hosted SearXNG, or DuckDuckGo when it isn't there."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

import httpx
from ddgs import DDGS

from ... import config
from ..market import Market

logger = logging.getLogger("ai_api.marketplaces")

TIMEOUT_S = 15


class SearchFailed(RuntimeError):
    """The search engine could not answer."""


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str


class SearchProvider(Protocol):
    name: str

    def results(self, query: str, market: Market, limit: int) -> list[SearchResult]: ...


class SearxngSearch:
    name = "searxng"

    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        self._base = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=TIMEOUT_S)

    def results(self, query: str, market: Market, limit: int) -> list[SearchResult]:
        try:
            response = self._client.get(f"{self._base}/search", params={
                "q": query, "format": "json", "language": market.locale,
                "engines": config.SEARXNG_ENGINES, "safesearch": 0})
            response.raise_for_status()
            found = response.json().get("results", [])
        except (httpx.HTTPError, ValueError) as error:
            raise SearchFailed(f"SearXNG: {error}") from error
        return [SearchResult(entry["url"], entry.get("title", "")) for entry in found
                if entry.get("url")][:limit]


class DuckDuckGoSearch:
    name = "duckduckgo"

    def results(self, query: str, market: Market, limit: int) -> list[SearchResult]:
        region = f"{market.country}-{market.language}".lower()
        try:
            found = list(DDGS().text(query, region=region, max_results=limit))
        except Exception as error:  # noqa: BLE001
            raise SearchFailed(f"DuckDuckGo: {error}") from error
        return [SearchResult(entry["href"], entry.get("title", "")) for entry in found
                if entry.get("href")]


def default_providers() -> list[SearchProvider]:
    """SearXNG when it is configured, then DuckDuckGo as the fallback."""
    providers: list[SearchProvider] = []
    if config.SEARXNG_URL:
        providers.append(SearxngSearch(config.SEARXNG_URL))
    providers.append(DuckDuckGoSearch())
    return providers
