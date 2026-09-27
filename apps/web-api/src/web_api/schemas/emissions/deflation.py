"""How a line's converted spend was taken back to the factor set's price year."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class EmissionDeflationRead(BaseModel):
    """`converted` × `base_index` ÷ `index` = `deflated`, in `base_year` money."""

    series: str
    label: str
    month: date
    index: Decimal
    base_year: int
    base_index: Decimal
    deflated: Decimal
