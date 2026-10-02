"""A product page's offers: from its structured data, and from its text by the LLM where the
data is missing or doesn't say whether VAT is included."""
from __future__ import annotations

import logging
from collections.abc import Callable

from ... import config
from ...parsing import json_format_hint, parse_model
from ..offer import Offer
from .page import Page
from .prices import parse_price
from .reply import PageOffer, PageOffers
from .structured import StructuredProduct, structured_products

logger = logging.getLogger("ai_api.marketplaces")

Ask = Callable[[str], str]
MAX_OFFERS_PER_PAGE = 3

_RULES = [
    "Read the products this web page offers for sale, with their prices. Only list a product "
    "whose price the page states; never guess one.",
    "price: the price of one sale unit as written. currency: its ISO code (DKK for kr.). "
    "vat_included: true when the price includes VAT (\"inkl. moms\", \"incl. VAT\"), false when "
    "it excludes it (\"ekskl. moms\", \"excl. VAT\"), null when the page doesn't say.",
    "pack: what one sale unit holds when it is more than one thing (\"8 ruller\", \"305 m\", "
    "\"pakke a 100 stk\"), else null. gtin, part_number, brand and model only when stated.",
    "availability and shipping: as the page states them, briefly, else null.",
]


class PageReader:
    def __init__(self, ask: Ask) -> None:
        self._ask = ask

    def offers(self, page: Page, *, seller: str, seller_country: str | None,
               vat_included: bool | None) -> list[Offer]:
        """The page's offers. `vat_included` is what the seller's prices usually are, used when
        the page's data doesn't say."""
        excerpt = page.markdown[:config.ALTERNATIVES_PAGE_CHARS]
        products = structured_products(page.html)[:MAX_OFFERS_PER_PAGE]
        if products and all(product.vat_included is not None or vat_included is not None
                            for product in products):
            return [_from_structured(product, page, seller, seller_country, vat_included,
                                     excerpt) for product in products]
        read = self._read(page, excerpt)
        if products:
            stated = next((offer.vat_included for offer in read
                           if offer.vat_included is not None), None)
            if stated is None:
                return []
            return [_from_structured(product, page, seller, seller_country, stated, excerpt)
                    for product in products]
        return [offer for entry in read[:MAX_OFFERS_PER_PAGE]
                if (offer := _from_text(entry, page, seller, seller_country, vat_included,
                                        excerpt)) is not None]

    def _read(self, page: Page, excerpt: str) -> list[PageOffer]:
        if not excerpt:
            return []
        prompt = "\n".join([*_RULES, "", f"Page: {page.url}", "", excerpt, "",
                            json_format_hint(PageOffers)])
        try:
            return parse_model(self._ask(prompt), PageOffers).offers
        except Exception as error:  # noqa: BLE001
            logger.warning("marketplaces: %s was not read: %s", page.url, error)
            return []


def _from_structured(product: StructuredProduct, page: Page, seller: str,
                     seller_country: str | None, vat_included: bool | None,
                     excerpt: str) -> Offer:
    description = "\n".join(part for part in (product.description, excerpt) if part)
    return Offer(seller=product.seller or seller, title=product.name, url=page.url,
                 price=product.price, currency=product.currency,
                 vat_included=product.vat_included if product.vat_included is not None
                 else bool(vat_included),
                 seller_country=seller_country,
                 description=description[:config.ALTERNATIVES_PAGE_CHARS],
                 gtin=product.gtin, part_number=product.part_number, brand=product.brand,
                 availability=product.availability)


def _from_text(entry: PageOffer, page: Page, seller: str, seller_country: str | None,
               vat_included: bool | None, excerpt: str) -> Offer | None:
    price = parse_price(entry.price)
    vat = entry.vat_included if entry.vat_included is not None else vat_included
    if price is None or not entry.currency or vat is None or not entry.title:
        return None
    return Offer(seller=seller, title=entry.title, url=page.url, price=price,
                 currency=entry.currency.upper(), vat_included=vat,
                 seller_country=seller_country, description=excerpt, pack=entry.pack,
                 gtin=entry.gtin, part_number=entry.part_number, brand=entry.brand,
                 model=entry.model, availability=entry.availability, shipping=entry.shipping)
