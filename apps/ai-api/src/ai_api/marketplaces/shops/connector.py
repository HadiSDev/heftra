"""The shop-search connector: each shop's own search, then the product pages it lists."""
from __future__ import annotations

from ... import config
from ..market import Market
from ..offer import Offer
from ..pages.page import Fetch
from ..pages.reader import PageReader
from .catalog import Shop, shops_in


class ShopSearch:
    name = "shops"

    def __init__(self, fetch: Fetch, reader: PageReader) -> None:
        self._fetch = fetch
        self._reader = reader

    def enabled(self) -> bool:
        return config.ALTERNATIVES_SHOPS_ENABLED

    def search(self, query: str, market: Market) -> list[Offer]:
        """Each shop's first product for the query, up to `ALTERNATIVES_PAGES_PER_ITEM`
        product pages, read into offers."""
        shops = shops_in(market.country)
        results = {page.url: page for page in self._fetch([shop.search(query) for shop in shops])}
        chosen: list[tuple[Shop, str]] = []
        for shop in shops:
            page = results.get(shop.search(query))
            link = next((link for link in page.links if shop.is_product(link)), None) \
                if page is not None else None
            if link is not None:
                chosen.append((shop, link))
        chosen = chosen[:config.ALTERNATIVES_PAGES_PER_ITEM]
        pages = {page.url: page for page in self._fetch([link for _, link in chosen])}
        offers: list[Offer] = []
        for shop, link in chosen:
            if link in pages:
                offers += self._reader.offers(pages[link], seller=shop.name,
                                              seller_country=shop.market,
                                              vat_included=shop.prices_include_vat)
        return offers
