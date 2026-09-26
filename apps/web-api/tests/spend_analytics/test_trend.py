"""Twelve months of spend, stacked by the five largest categories, the rest and the uncategorized."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from spend_books import Books
from web_api.spend_analytics.periods import Period
from web_api.spend_analytics.trend import spend_trend

Q3 = Period(date(2026, 7, 1), date(2026, 9, 30))


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _buy(books: Books, on: date, amount: str, category: str | None) -> None:
    status = "verified" if category else "uncategorized"
    books.purchase(on, amount, vendor=books.supplier(f"{category} ApS"),
                   lines=[(amount, category, None, status)])


def test_twelve_months_are_given_with_zeros_where_nothing_was_spent(session):
    books = Books(session)
    _buy(books, date(2026, 9, 3), "30.00", "Technology")

    (row,) = spend_trend(session, [books.company.id], Q3).rows

    assert len(row.months) == 12
    assert row.months[-1] == date(2026, 9, 1)
    (series,) = row.series
    assert series.amounts[-1] == Decimal("30.00")
    assert series.amounts[:-1] == [Decimal("0")] * 11


def test_the_five_largest_categories_are_named_and_the_rest_summed(session):
    books = Books(session)
    for rank, name in enumerate(["A", "B", "C", "D", "E", "F", "G"]):
        _buy(books, date(2026, 8, 1), str(100 - rank), name)
    _buy(books, date(2026, 8, 2), "7.00", None)

    (row,) = spend_trend(session, [books.company.id], Q3).rows

    assert [(s.kind, s.name) for s in row.series] == [
        ("category", "A"), ("category", "B"), ("category", "C"), ("category", "D"),
        ("category", "E"), ("other", None), ("not_categorized", None),
    ]
    assert row.series[5].amounts[-2] == Decimal("95") + Decimal("94")
    assert row.series[6].amounts[-2] == Decimal("7.00")


def test_the_top_categories_are_chosen_over_the_whole_twelve_months(session):
    books = Books(session)
    _buy(books, date(2025, 11, 1), "500.00", "Rent")
    _buy(books, date(2026, 9, 1), "10.00", "Coffee")

    (row,) = spend_trend(session, [books.company.id], Q3).rows

    assert [s.name for s in row.series] == ["Rent", "Coffee"]
