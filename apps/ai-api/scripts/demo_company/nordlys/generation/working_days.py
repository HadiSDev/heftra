"""The months the books cover and their working days."""
from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta

from ..settings import FIRST_DAY, LAST_DAY

SATURDAY = 5


def months() -> Iterator[date]:
    """The first day of every month from the first day to the last."""
    month = FIRST_DAY.replace(day=1)
    while month <= LAST_DAY:
        yield month
        month = (month + timedelta(days=32)).replace(day=1)


def working_days(month: date, since: date | None = None) -> list[date]:
    """The month's weekdays within the books, from `since` when given."""
    following = (month + timedelta(days=32)).replace(day=1)
    days = []
    day = month
    while day < following and day <= LAST_DAY:
        after_start = since is None or day >= since
        if day.weekday() < SATURDAY and day >= FIRST_DAY and after_start:
            days.append(day)
        day += timedelta(days=1)
    return days
