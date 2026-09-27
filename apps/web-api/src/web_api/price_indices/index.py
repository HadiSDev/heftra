"""One price index series held in memory: a year's average and the value for a date."""
from __future__ import annotations

from bisect import bisect_right
from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from ..db.models import PriceIndexValue
from .values import IndexValue

MONTHS_IN_YEAR = 12


class PriceIndex:
    """A series' monthly values, in date order."""

    def __init__(self, values: list[IndexValue]) -> None:
        self._values = sorted(values)
        self._months = [value.month for value in self._values]

    @classmethod
    def load(cls, session: Session, series: str) -> PriceIndex:
        rows = session.exec(
            select(PriceIndexValue.month, PriceIndexValue.value)
            .where(PriceIndexValue.series == series)
        ).all()
        return cls([IndexValue(month, value) for month, value in rows])

    @property
    def latest_month(self) -> date | None:
        return self._months[-1] if self._months else None

    def average(self, year: int) -> Decimal | None:
        """The mean of the year's twelve months, or None when any month is missing."""
        in_year = [value.value for value in self._values if value.month.year == year]
        if len(in_year) != MONTHS_IN_YEAR:
            return None
        return sum(in_year, Decimal(0)) / MONTHS_IN_YEAR

    def at(self, day: date) -> IndexValue | None:
        """The value for `day`'s month, else the latest earlier one; None before the first."""
        position = bisect_right(self._months, day.replace(day=1))
        if position == 0:
            return None
        return self._values[position - 1]
