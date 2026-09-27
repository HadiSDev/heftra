"""The period of a volume commitment that a date falls in."""
from __future__ import annotations

from datetime import date, timedelta
from typing import NamedTuple

MONTHS_IN = {"month": 1, "quarter": 3, "year": 12}


class CommitmentPeriod(NamedTuple):
    start: date
    end: date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def commitment_period(kind: str | None, starts_on: date, ends_on: date | None,
                      today: date) -> CommitmentPeriod:
    """The month, quarter or year counted from the agreement's start that holds `today`.

    Any other `kind` means the whole agreement, which must then have an end date; without one the
    period is a year from the start.
    """
    months = MONTHS_IN.get(kind or "")
    if months is None:
        end = ends_on or _add_months(starts_on, 12) - timedelta(days=1)
        return CommitmentPeriod(starts_on, end)
    start = starts_on
    while True:
        following = _add_months(start, months)
        if following > today or (ends_on is not None and following > ends_on):
            end = following - timedelta(days=1)
            return CommitmentPeriod(start, min(end, ends_on) if ends_on else end)
        start = following


def _add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, min(day.day, _days_in(year, month)))


def _days_in(year: int, month: int) -> int:
    following = date(year + month // 12, month % 12 + 1, 1)
    return (following - timedelta(days=1)).day
