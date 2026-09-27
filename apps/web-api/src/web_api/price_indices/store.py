"""Replacing a series' stored values."""
from __future__ import annotations

from sqlalchemy import delete
from sqlmodel import Session

from ..db.models import PriceIndexValue
from .values import IndexValue


def replace_series(session: Session, series: str, values: list[IndexValue], source: str) -> None:
    """The series' values become `values`; the caller commits."""
    session.exec(delete(PriceIndexValue).where(PriceIndexValue.series == series))
    session.add_all(
        PriceIndexValue(series=series, month=value.month, value=value.value, source=source)
        for value in values
    )
