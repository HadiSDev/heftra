"""The price index a factor set's estimates are deflated with."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class PriceIndexRead(BaseModel):
    series: str
    label: str
    latest_month: date | None = None
