"""Something the demo company buys, described the same way by every supplier selling it."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductSpec:
    """`leaf` is the spend category's code and `sector` the emission sector's code; `spec` is the
    stored specification an item of this product carries."""

    key: str
    name: str
    description: str
    unit: str | None
    leaf: str
    sector: str
    spec: dict
