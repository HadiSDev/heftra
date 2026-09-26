"""The period a spend report covers and the one it is compared with."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class PeriodRead(BaseModel):
    start: date
    end: date


class ReportPeriods(BaseModel):
    """The period asked for and the comparison period the report measured it against."""

    period: PeriodRead
    comparison: PeriodRead
