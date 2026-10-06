"""Filling the shared ECB rate cache for the days the demo company spent on, so the first
emissions report doesn't fetch hundreds of days' rates while the page waits."""
from __future__ import annotations

from datetime import date

from sqlmodel import Session

from web_api.fx.service import FxService

from ..settings import CURRENCY


def warm_rates(session: Session, days: set[date], factor_currency: str) -> int:
    """Look up each day's rate into the factor set's currency; returns how many days lack one.
    Commits."""
    fx = FxService(session)
    fx.prefetch(days)
    missing = 0
    for day in sorted(days):
        if fx.get_rate(CURRENCY, factor_currency, day) is None:
            missing += 1
    session.commit()
    return missing
