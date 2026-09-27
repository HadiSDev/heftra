"""Which price index deflates money in which currency."""
from __future__ import annotations

from typing import NamedTuple


class PriceSeries(NamedTuple):
    """A stored series' id and the name it is shown under."""

    id: str
    label: str


US_CPI = PriceSeries(id="CPIAUCSL", label="US CPI")

_BY_CURRENCY = {"USD": US_CPI}


def index_for_currency(currency: str) -> PriceSeries | None:
    return _BY_CURRENCY.get(currency.upper())
