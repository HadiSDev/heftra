"""What an estimate needs to know about a voucher and its lines."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import NamedTuple


class LineInput(NamedTuple):
    line_id: str
    base_amount: Decimal | None
    sector_id: str | None


class VoucherInput(NamedTuple):
    """A voucher's net base-currency spend, when it fell, where it was bought, and its lines."""

    amount: Decimal | None
    currency: str | None
    unconverted: bool
    spent_on: date
    supplier_country: str | None
    company_country: str | None
    lines: list[LineInput]
