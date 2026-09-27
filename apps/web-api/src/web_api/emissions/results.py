"""An estimate's outcome for a voucher and for each of its lines."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import NamedTuple

from .status import EmissionsStatus


class LineEmissions(NamedTuple):
    """A line's kg CO2e and every figure it was multiplied out from."""

    kg_co2e: Decimal
    area: str
    sector_id: str
    spend: Decimal
    currency: str
    rate: Decimal
    rate_date: date
    factor: Decimal
    factor_currency: str


class VoucherEmissions(NamedTuple):
    """The voucher's kg CO2e, the base-currency spend it covers, and each estimated line."""

    kg_co2e: Decimal | None
    status: EmissionsStatus
    estimated_spend: Decimal
    lines: dict[str, LineEmissions]
