"""Planning one invoice line: its quantity, price, discount and how sure the categorization was."""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ..catalog.shapes import OfferSpec, ProductSpec
from ..settings import MONEY
from .planned import PlannedLine

AI_CATEGORIZED = "ai_categorized"
VERIFIED = "verified"

UNSURE_SHARE = 0.015
VERIFIED_SHARE = 0.05
LUMP_SUM_ROUNDING = Decimal("10")
LUMP_SUM_FROM = Decimal("1000")
HUNDRED = Decimal(100)


@dataclass(frozen=True)
class Categorization:
    status: str
    confidence: Decimal
    sector_confidence: Decimal


class LinePlanner:
    """Draws lines from a seeded random source, so the same seed plans the same lines."""

    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def order(self, offer: OfferSpec, on: date, sequence: int, scale: float) -> PlannedLine:
        """A line ordering the offer on a day, its quantity scaled by how busy the month is."""
        low, high = offer.quantity
        drawn = Decimal(str(self._rng.uniform(float(low), float(high)) * scale))
        quantity = max(offer.step, (drawn / offer.step).quantize(Decimal(1), ROUND_HALF_UP)
                       * offer.step)
        unit_price = self._price(offer, on)
        listed = (quantity * unit_price).quantize(MONEY, ROUND_HALF_UP)
        discount = self._discount(offer, on, listed)
        amount = listed - discount if discount is not None else listed
        return self._line(offer.product, sequence, quantity, unit_price, discount, amount)

    def lump_sum(self, product: ProductSpec, sequence: int, amount: Decimal) -> PlannedLine:
        """A line of one unit at a stated amount, such as a stage payment."""
        return self._line(product, sequence, Decimal(1), amount, None, amount)

    def _line(self, product: ProductSpec, sequence: int, quantity: Decimal, unit_price: Decimal,
              discount: Decimal | None, amount: Decimal) -> PlannedLine:
        categorization = self._categorization()
        return PlannedLine(sequence=sequence, product=product, quantity=quantity,
                           unit_price=unit_price, discount=discount, amount=amount,
                           status=categorization.status, confidence=categorization.confidence,
                           sector_confidence=categorization.sector_confidence)

    def _price(self, offer: OfferSpec, on: date) -> Decimal:
        price = offer.price_on(on)
        if not offer.price_jitter:
            return price
        varied = price * Decimal(str(1 + self._rng.uniform(-offer.price_jitter,
                                                           offer.price_jitter)))
        if varied >= LUMP_SUM_FROM:
            return (varied / LUMP_SUM_ROUNDING).quantize(Decimal(1), ROUND_HALF_UP) \
                * LUMP_SUM_ROUNDING
        return varied.quantize(MONEY, ROUND_HALF_UP)

    def _discount(self, offer: OfferSpec, on: date, listed: Decimal) -> Decimal | None:
        if offer.discount_percent is None or offer.discount_since is None:
            return None
        if on < offer.discount_since or self._rng.random() >= offer.discount_share:
            return None
        return (listed * offer.discount_percent / HUNDRED).quantize(MONEY, ROUND_HALF_UP)

    def _categorization(self) -> Categorization:
        sector = self._confidence(0.72, 0.96)
        if self._rng.random() < UNSURE_SHARE:
            return Categorization(AI_CATEGORIZED, self._confidence(0.41, 0.58), sector)
        status = VERIFIED if self._rng.random() < VERIFIED_SHARE else AI_CATEGORIZED
        return Categorization(status, self._confidence(0.82, 0.99), sector)

    def _confidence(self, low: float, high: float) -> Decimal:
        return Decimal(str(round(self._rng.uniform(low, high), 3)))
