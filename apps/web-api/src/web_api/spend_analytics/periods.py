"""Reporting periods: a span of days, the equal span before it, and calendar months."""
from __future__ import annotations

from dataclasses import dataclass
import calendar
from datetime import date, timedelta


@dataclass(frozen=True)
class Period:
    """The days from `start` to `end`, both included."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("A period cannot end before it starts.")

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def months(self) -> int:
        """How many calendar months the period touches."""
        return (self.end.year - self.start.year) * 12 + self.end.month - self.start.month + 1

    def comparison(self) -> Period:
        """The period this one is compared with.

        One starting on the first of a month is compared with the same days as many calendar
        months earlier; any other with as many days ending the day before it starts.
        """
        if self.start.day == 1:
            return Period(
                shift_months(self.start, -self.months), shift_months(self.end, -self.months)
            )
        end = self.start - timedelta(days=1)
        return Period(end - timedelta(days=self.days - 1), end)

    def contains(self, day: date) -> bool:
        return self.start <= day <= self.end


def month_start(day: date) -> date:
    return day.replace(day=1)


def trailing_months(end: date, count: int = 12) -> list[date]:
    """The first days of the `count` calendar months ending with `end`'s month, oldest first."""
    months = [month_start(end)]
    while len(months) < count:
        previous = months[0] - timedelta(days=1)
        months.insert(0, month_start(previous))
    return months


def months_span(end: date, count: int = 12) -> Period:
    """The days of the `count` calendar months ending with `end`'s month, through `end`."""
    return Period(trailing_months(end, count)[0], end)


def shift_months(day: date, months: int) -> date:
    """The same day `months` calendar months away; a month's last day stays its last day."""
    index = day.year * 12 + day.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    last = calendar.monthrange(year, month)[1]
    if day.day == calendar.monthrange(day.year, day.month)[1]:
        return date(year, month, last)
    return date(year, month, min(day.day, last))
