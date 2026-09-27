"""Replacing a series from its CSV text, as the CLI and the admin refresh both do."""
from __future__ import annotations

from datetime import date
from typing import NamedTuple

from sqlmodel import Session

from .csv_file import SeriesFileError, parse_series_csv
from .store import replace_series


class StoredSeries(NamedTuple):
    months: int
    latest_month: date


def store_series(session: Session, series: str, text: str, source: str) -> StoredSeries:
    """Parse `text` and replace the series with it; the caller commits."""
    values = parse_series_csv(text, series)
    if not values:
        raise SeriesFileError(f"{series} has no values")
    replace_series(session, series, values, source)
    return StoredSeries(months=len(values), latest_month=values[-1].month)
