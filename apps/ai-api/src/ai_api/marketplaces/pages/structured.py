"""The schema.org Product and Offer data shops embed in their pages, in JSON-LD or microdata."""
from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal

from bs4 import BeautifulSoup, Tag

from .prices import parse_price

logger = logging.getLogger("ai_api.marketplaces")

_GTIN_KEYS = ("gtin13", "gtin", "gtin14", "gtin12", "gtin8")


@dataclass(frozen=True)
class StructuredProduct:
    """`vat_included` is None when the page doesn't say."""

    name: str
    price: Decimal
    currency: str
    description: str = ""
    sku: str | None = None
    part_number: str | None = None
    gtin: str | None = None
    brand: str | None = None
    availability: str | None = None
    seller: str | None = None
    vat_included: bool | None = None


def structured_products(html: str) -> list[StructuredProduct]:
    """The products with a price and currency the page states, from JSON-LD first."""
    soup = BeautifulSoup(html, "lxml")
    found = [product for node in _json_ld(soup) if (product := _from_json(node)) is not None]
    if found:
        return found
    return [product for element in soup.find_all(itemtype=_is_product)
            if (product := _from_microdata(element)) is not None]


def _json_ld(soup: BeautifulSoup) -> Iterator[dict]:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            logger.info("marketplaces: a page's JSON-LD did not parse")
            continue
        yield from _walk(data)


def _walk(data: object) -> Iterator[dict]:
    if isinstance(data, list):
        for entry in data:
            yield from _walk(entry)
    elif isinstance(data, dict):
        if _is_type(data.get("@type"), "Product"):
            yield data
        for key in ("@graph", "mainEntity", "itemListElement", "item"):
            if key in data:
                yield from _walk(data[key])


def _is_type(value: object, wanted: str) -> bool:
    types = value if isinstance(value, list) else [value]
    return any(isinstance(entry, str) and entry.split("/")[-1] == wanted for entry in types)


def _from_json(node: dict) -> StructuredProduct | None:
    offer = _first_offer(node.get("offers"))
    if offer is None:
        return None
    specification = offer.get("priceSpecification")
    if isinstance(specification, list):
        specification = specification[0] if specification else None
    specification = specification if isinstance(specification, dict) else {}
    price = parse_price(offer.get("price", offer.get("lowPrice", specification.get("price"))))
    currency = offer.get("priceCurrency") or specification.get("priceCurrency")
    if price is None or not currency:
        return None
    vat = specification.get("valueAddedTaxIncluded")
    return StructuredProduct(
        name=str(node.get("name") or ""), price=price, currency=str(currency).upper(),
        description=str(node.get("description") or ""),
        sku=_text(node.get("sku")), part_number=_text(node.get("mpn")),
        gtin=next((_text(node.get(key)) for key in _GTIN_KEYS if node.get(key)), None),
        brand=_name(node.get("brand")), availability=_short(offer.get("availability")),
        seller=_name(offer.get("seller")),
        vat_included=_boolean(vat))


def _first_offer(offers: object) -> dict | None:
    if isinstance(offers, list):
        return next((offer for offer in offers if isinstance(offer, dict)), None)
    if isinstance(offers, dict):
        nested = offers.get("offers")
        if nested and _is_type(offers.get("@type"), "AggregateOffer") and "lowPrice" not in offers:
            return _first_offer(nested)
        return offers
    return None


def _is_product(value: object) -> bool:
    return isinstance(value, str) and "schema.org/Product" in value


def _from_microdata(element: Tag) -> StructuredProduct | None:
    def prop(name: str) -> str | None:
        found = element.find(itemprop=name)
        if found is None:
            return None
        return found.get("content") or found.get("href") or found.get_text(" ", strip=True)

    price = parse_price(prop("price"))
    currency = prop("priceCurrency")
    if price is None or not currency:
        return None
    return StructuredProduct(
        name=prop("name") or "", price=price, currency=currency.upper(),
        description=prop("description") or "", sku=prop("sku"), part_number=prop("mpn"),
        gtin=next((value for key in _GTIN_KEYS if (value := prop(key))), None),
        brand=prop("brand"), availability=_short(prop("availability")))


def _name(value: object) -> str | None:
    if isinstance(value, dict):
        return _text(value.get("name"))
    return _text(value)


def _text(value: object) -> str | None:
    if value is None or isinstance(value, (dict, list)):
        return None
    text = str(value).strip()
    return text or None


def _short(value: object) -> str | None:
    text = _text(value)
    return text.split("/")[-1] if text else None


def _boolean(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
    return None
