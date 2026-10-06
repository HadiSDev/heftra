"""How busy a Danish contractor is through the year, and how the business grows: winter and the
July industrial holiday are quiet, spring and early autumn are busiest."""
from __future__ import annotations

from datetime import date

from ..settings import FIRST_DAY

BUSY = {1: 0.70, 2: 0.75, 3: 0.95, 4: 1.05, 5: 1.15, 6: 1.20, 7: 0.80, 8: 1.15, 9: 1.25,
        10: 1.20, 11: 1.00, 12: 0.70}

YEARLY_GROWTH = 0.09


def activity(month: date) -> float:
    """The month's activity against an average month of the first year."""
    years = ((month.year - FIRST_DAY.year) * 12 + month.month - FIRST_DAY.month) / 12
    return BUSY[month.month] * (1 + YEARLY_GROWTH * years)
