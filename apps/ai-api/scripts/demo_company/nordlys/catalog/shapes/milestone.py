"""A one-off large invoice, such as a stage payment or the yearly audit."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .product import ProductSpec


@dataclass(frozen=True)
class MilestoneSpec:
    on: date
    supplier: str
    product: ProductSpec
    amount: Decimal
