"""Price lists and order quantities, written briefly."""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ..settings import FIRST_DAY, MONEY
from .shapes import PricePoint

NEW_YEAR = date(2026, 1, 1)


def rising(base: str, rise: str = "0.03") -> tuple[PricePoint, ...]:
    """`base` until the new year, then raised by `rise`."""
    price = Decimal(base)
    raised = (price * (1 + Decimal(rise))).quantize(MONEY, ROUND_HALF_UP)
    return PricePoint(FIRST_DAY, price), PricePoint(NEW_YEAR, raised)


def fixed(price: str) -> tuple[PricePoint, ...]:
    return (PricePoint(FIRST_DAY, Decimal(price)),)


def stepped(base: str, *steps: tuple[date, str]) -> tuple[PricePoint, ...]:
    """`base` from the first day, then each `(since, price)` in turn."""
    return (PricePoint(FIRST_DAY, Decimal(base)),
            *(PricePoint(since, Decimal(price)) for since, price in steps))


def quantity(low: str, high: str) -> tuple[Decimal, Decimal]:
    return Decimal(low), Decimal(high)
