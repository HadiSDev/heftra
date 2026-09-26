"""Spend by category with its second level, and by supplier, in both periods."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from spend_books import Books
from web_api.spend_analytics.breakdown import spend_breakdown
from web_api.spend_analytics.periods import Period

Q3 = Period(date(2026, 7, 1), date(2026, 9, 30))


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def test_categories_come_with_their_children_in_both_periods(session):
    books = Books(session)
    shop = books.supplier("Shop ApS")
    books.purchase(date(2026, 8, 1), "300.00", vendor=shop, lines=[
        ("200", "Technology", "Software", "verified"), ("100", "Technology", "Hardware", "verified"),
    ])
    books.purchase(date(2026, 5, 1), "50.00", vendor=shop, lines=[("50", "Technology", "Hardware", "verified")])
    books.purchase(date(2026, 8, 2), "400.00", vendor=shop, lines=[("400", "Facilities", "Rent", "verified")])

    (row,) = spend_breakdown(session, [books.company.id], Q3).rows

    assert [(c.name, c.spend, c.comparison_spend) for c in row.categories] == [
        ("Facilities", Decimal("400.00"), Decimal("0")),
        ("Technology", Decimal("300.00"), Decimal("50.00")),
    ]
    assert [(c.name, c.spend, c.comparison_spend) for c in row.categories[1].children] == [
        ("Software", Decimal("200.00"), Decimal("0")),
        ("Hardware", Decimal("100.00"), Decimal("50.00")),
    ]
    assert row.spend == Decimal("700.00")


def test_the_uncategorized_spend_comes_last(session):
    books = Books(session)
    books.purchase(date(2026, 8, 1), "900.00")
    books.purchase(date(2026, 8, 2), "10.00", vendor=books.supplier("A ApS"),
                   lines=[("10", "Technology", "Software", "verified")])

    (row,) = spend_breakdown(session, [books.company.id], Q3).rows

    assert [(c.name, c.spend) for c in row.categories] == [
        ("Technology", Decimal("10.00")), (None, Decimal("900.00")),
    ]


def test_the_top_suppliers_come_largest_first_with_both_periods(session):
    books = Books(session)
    big, small, gone = books.supplier("Big ApS"), books.supplier("Small ApS"), books.supplier("Gone ApS")
    books.purchase(date(2026, 8, 1), "500.00", vendor=big)
    books.purchase(date(2026, 5, 1), "200.00", vendor=big)
    books.purchase(date(2026, 8, 1), "50.00", vendor=small)
    books.purchase(date(2026, 5, 1), "70.00", vendor=gone)

    (row,) = spend_breakdown(session, [books.company.id], Q3).rows

    assert [(s.name, s.spend, s.comparison_spend) for s in row.suppliers] == [
        ("Big ApS", Decimal("500.00"), Decimal("200.00")),
        ("Small ApS", Decimal("50.00"), Decimal("0")),
    ]


def test_the_supplier_list_is_limited_with_ties_broken_by_name(session):
    books = Books(session)
    for name in ("Charlie ApS", "Alpha ApS", "Bravo ApS"):
        books.purchase(date(2026, 8, 1), "10.00", vendor=books.supplier(name))

    (row,) = spend_breakdown(session, [books.company.id], Q3, limit=2).rows

    assert [s.name for s in row.suppliers] == ["Alpha ApS", "Bravo ApS"]
