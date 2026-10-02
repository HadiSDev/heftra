"""The marketplace connectors that are enabled, sharing one page fetcher and host limiter."""
from __future__ import annotations

from collections.abc import Callable

from .. import config
from .distributors.digikey import DigiKey
from .distributors.farnell import Farnell
from .distributors.mouser import Mouser
from .limiter import HostLimiter
from .pages.fetch import PageFetcher
from .pages.reader import PageReader
from .shops.connector import ShopSearch
from .source import OfferSource
from .web.connector import WebSearch
from .web.search import default_providers

LIMITER = HostLimiter(config.ALTERNATIVES_HOST_INTERVAL_S)


def enabled_connectors(ask: Callable[[str], str]) -> list[OfferSource]:
    fetch = PageFetcher(LIMITER)
    reader = PageReader(ask)
    connectors: list[OfferSource] = [ShopSearch(fetch, reader),
                                     WebSearch(default_providers(), fetch, reader),
                                     Farnell(), Mouser(), DigiKey()]
    return [connector for connector in connectors if connector.enabled()]
