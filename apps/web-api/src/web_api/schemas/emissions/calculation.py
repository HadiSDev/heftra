"""How a line's emissions were multiplied out, figure by figure."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from .deflation import EmissionDeflationRead
from .sectors import EmissionSectorRead


class EmissionCalculationRead(BaseModel):
    """`spend` × `rate` = `converted`, deflated when `deflation` is set; that × `factor` = `kg_co2e`."""

    spend: Decimal
    currency: str
    rate: Decimal
    rate_date: date
    converted: Decimal
    deflation: EmissionDeflationRead | None = None
    factor: Decimal
    factor_currency: str
    factor_area: str
    sector: EmissionSectorRead | None = None
    kg_co2e: Decimal
