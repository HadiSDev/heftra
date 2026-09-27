"""Reading a price index series from a FRED-style CSV: a date column and one named after the series."""
from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from .values import IndexValue

DATE_COLUMNS = ("observation_date", "DATE", "date")
MISSING = {"", "."}


class SeriesFileError(ValueError):
    """The CSV isn't a price index series file."""


def parse_series_csv(text: str, series: str) -> list[IndexValue]:
    """Every month with a value, in date order. Months with a blank or "." value are left out."""
    reader = csv.DictReader(io.StringIO(text))
    columns = reader.fieldnames or []
    date_column = next((column for column in DATE_COLUMNS if column in columns), None)
    if date_column is None:
        raise SeriesFileError(f"no date column; expected one of {', '.join(DATE_COLUMNS)}")
    if series not in columns:
        raise SeriesFileError(f"no {series} column")

    values = []
    for number, row in enumerate(reader, start=2):
        raw = (row.get(series) or "").strip()
        if raw in MISSING:
            continue
        try:
            day = date.fromisoformat(row[date_column].strip())
            value = Decimal(raw)
        except (ValueError, InvalidOperation) as error:
            raise SeriesFileError(f"line {number}: {error}") from error
        values.append(IndexValue(day.replace(day=1), value))
    return sorted(values)
