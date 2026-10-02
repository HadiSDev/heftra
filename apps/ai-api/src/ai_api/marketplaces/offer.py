"""A product offered for sale, as a connector reads it."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class PriceBreak:
    """The price of one sale unit from `quantity` sale units up."""

    quantity: int
    price: Decimal


@dataclass(frozen=True)
class Offer:
    """`price` is for one sale unit, which `pack` describes when it holds more than one thing
    ("8 ruller", "305 m"); `description` is what the seller says of the product."""

    seller: str
    title: str
    url: str
    price: Decimal
    currency: str
    vat_included: bool
    seller_country: str | None = None
    description: str = ""
    pack: str | None = None
    gtin: str | None = None
    part_number: str | None = None
    brand: str | None = None
    model: str | None = None
    price_breaks: tuple[PriceBreak, ...] = field(default_factory=tuple)
    availability: str | None = None
    shipping: str | None = None
