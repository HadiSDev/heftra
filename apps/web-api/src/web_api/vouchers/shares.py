"""Sharing a voucher's amount out between its parts, in cents that add up exactly."""
from __future__ import annotations

from decimal import Decimal
from typing import TypeVar

from .amounts import ZERO

CENT = Decimal("0.01")

Key = TypeVar("Key")


def split(amount: Decimal, weights: dict[Key, Decimal]) -> dict[Key, Decimal]:
    """`amount` shared out in proportion to `weights`, or nothing when they add up to zero or less.

    The cent left over by rounding goes to the largest part.
    """
    total = sum(weights.values(), ZERO)
    if total <= 0:
        return {}
    parts = {key: (amount * weight / total).quantize(CENT) for key, weight in weights.items()}
    remainder = amount - sum(parts.values(), ZERO)
    if remainder:
        largest = max(parts, key=lambda key: abs(parts[key]))
        parts[largest] += remainder
    return parts
