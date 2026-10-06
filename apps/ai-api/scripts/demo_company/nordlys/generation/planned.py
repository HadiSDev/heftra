"""The purchases the demo company made, planned before anything is written."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from ..catalog.shapes import ProductSpec, SupplierSpec
from ..settings import MONEY, VAT_RATE


@dataclass(frozen=True)
class PlannedLine:
    """`unit_price` is the list price; `amount` is net of VAT and of any `discount`."""

    sequence: int
    product: ProductSpec
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal | None
    amount: Decimal
    status: str
    confidence: Decimal
    sector_confidence: Decimal


@dataclass(frozen=True)
class PlannedInvoice:
    key: str
    supplier: SupplierSpec
    number: str
    on: date
    lines: tuple[PlannedLine, ...]

    @property
    def net(self) -> Decimal:
        return sum((line.amount for line in self.lines), Decimal(0))

    @property
    def tax(self) -> Decimal:
        return (self.net * VAT_RATE).quantize(MONEY, ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        return self.net + self.tax
