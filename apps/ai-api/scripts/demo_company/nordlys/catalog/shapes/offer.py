"""A product as one supplier sells it: its prices over time and the quantities ordered."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .product import ProductSpec


@dataclass(frozen=True)
class PricePoint:
    """The unit price from `since` until the next point."""

    since: date
    price: Decimal


@dataclass(frozen=True)
class OfferSpec:
    """`quantity` is the range one line orders, rounded to `step`; `weight` how often the product
    is on an invoice; `price_jitter` how far a lump-sum price varies either way; a share
    `discount_share` of lines from `discount_since` carry `discount_percent` off the list price."""

    product: ProductSpec
    prices: tuple[PricePoint, ...]
    quantity: tuple[Decimal, Decimal]
    step: Decimal = Decimal("1")
    weight: float = 1.0
    price_jitter: float = 0.0
    discount_percent: Decimal | None = None
    discount_since: date | None = None
    discount_share: float = 0.0

    def price_on(self, day: date) -> Decimal:
        current = self.prices[0].price
        for point in self.prices:
            if point.since <= day:
                current = point.price
        return current
