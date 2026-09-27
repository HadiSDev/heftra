"""Deflating money converted at the voucher date to the factor set's price year."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import NamedTuple

from sqlmodel import Session

from ..db.models import EmissionFactorSet
from ..price_indices.index import PriceIndex
from ..price_indices.series import PriceSeries, index_for_currency


class Deflation(NamedTuple):
    """The index values one line's spend was deflated with."""

    series: str
    label: str
    month: date
    index: Decimal
    base_year: int
    base_index: Decimal

    @property
    def ratio(self) -> Decimal:
        return self.base_index / self.index


class Deflator:
    """A series and its average over the price year, ready to deflate any date's money."""

    def __init__(self, series: PriceSeries, base_year: int, base_index: Decimal,
                 index: PriceIndex) -> None:
        self.series = series
        self.base_year = base_year
        self.base_index = base_index
        self.index = index

    @classmethod
    def for_factor_set(cls, session: Session, factor_set: EmissionFactorSet) -> Deflator | None:
        """None when the set's currency has no index, or its price year isn't complete."""
        series = index_for_currency(factor_set.currency)
        if series is None:
            return None
        index = PriceIndex.load(session, series.id)
        base_index = index.average(factor_set.price_year)
        if base_index is None:
            return None
        return cls(series, factor_set.price_year, base_index, index)

    def for_date(self, day: date) -> Deflation | None:
        value = self.index.at(day)
        if value is None:
            return None
        return Deflation(
            series=self.series.id, label=self.series.label, month=value.month,
            index=value.value, base_year=self.base_year, base_index=self.base_index,
        )
