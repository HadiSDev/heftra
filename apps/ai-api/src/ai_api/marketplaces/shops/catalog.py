"""The shop list: which shops are searched in each market, and how."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus, urlparse

import yaml

from ... import config

BUNDLED = Path(__file__).with_name("shops.yaml")
_PRODUCT_PATH = re.compile(r"/product/|/p/|[/-]\d{5,}(?:[/?#.-]|$)")


@dataclass(frozen=True)
class Shop:
    name: str
    market: str
    search_url: str
    product_link: re.Pattern | None
    prices_include_vat: bool | None

    def search(self, query: str) -> str:
        return self.search_url.replace("{query}", quote_plus(query))

    def is_product(self, url: str) -> bool:
        if self.product_link is not None:
            return self.product_link.search(url) is not None
        same_host = urlparse(url).hostname == urlparse(self.search_url).hostname
        return same_host and _PRODUCT_PATH.search(urlparse(url).path) is not None


def shops_in(country: str) -> list[Shop]:
    return [shop for shop in _catalog(config.ALTERNATIVES_SHOPS_FILE or str(BUNDLED))
            if shop.market == country]


@lru_cache(maxsize=4)
def _catalog(path: str) -> tuple[Shop, ...]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return tuple(
        Shop(name=entry["name"], market=entry["market"].upper(), search_url=entry["search_url"],
             product_link=re.compile(entry["product_link"]) if entry.get("product_link")
             else None,
             prices_include_vat=entry.get("prices_include_vat"))
        for entry in data.get("shops", []))
