"""New suppliers, the biggest rises, recurring spend and the largest uncategorized vouchers."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from spend_books import Books
from web_api.spend_analytics.insights import spend_insights
from web_api.spend_analytics.periods import Period

Q3 = Period(date(2026, 7, 1), date(2026, 9, 30))


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _row(session, books: Books):
    (row,) = spend_insights(session, [books.company.id], Q3).rows
    return row


def test_a_supplier_first_invoiced_in_the_period_is_new(session):
    books = Books(session)
    books.purchase(date(2026, 8, 3), "120.00", vendor=books.supplier("Fresh ApS"))
    old = books.supplier("Old ApS")
    books.purchase(date(2026, 1, 3), "10.00", vendor=old)
    books.purchase(date(2026, 8, 3), "10.00", vendor=old)

    assert [(s.name, s.amount) for s in _row(session, books).new_suppliers] == [
        ("Fresh ApS", Decimal("120.00")),
    ]


def test_only_rises_are_increases_and_new_suppliers_are_not_repeated(session):
    books = Books(session)
    up, down = books.supplier("Up ApS"), books.supplier("Down ApS")
    for vendor, before, now in ((up, "100.00", "400.00"), (down, "400.00", "100.00")):
        books.purchase(date(2026, 5, 3), before, vendor=vendor)
        books.purchase(date(2026, 8, 3), now, vendor=vendor)
    books.purchase(date(2026, 8, 3), "999.00", vendor=books.supplier("Fresh ApS"))

    increases = _row(session, books).increases

    assert [(s.name, s.amount, s.comparison_amount) for s in increases] == [
        ("Up ApS", Decimal("400.00"), Decimal("100.00")),
    ]


def test_a_supplier_billed_in_three_of_six_months_is_recurring(session):
    books = Books(session)
    saas, once = books.supplier("SaaS ApS"), books.supplier("Once ApS")
    for month, amount in ((5, "390.00"), (7, "400.00"), (8, "410.00"), (9, "400.00")):
        books.purchase(date(2026, month, 2), amount, vendor=saas)
    books.purchase(date(2026, 9, 2), "5000.00", vendor=once)

    recurring = _row(session, books).recurring

    assert [(s.name, s.amount, s.active_months) for s in recurring] == [
        ("SaaS ApS", Decimal("400.00"), 4),
    ]


def test_the_largest_uncategorized_vouchers_are_listed_with_how_to_open_them(session):
    books = Books(session)
    shop = books.supplier("Shop ApS")
    invoice = books.purchase(date(2026, 8, 3), "100.00", vendor=shop, lines=[
        ("60", "Technology", "Software", "verified"), ("40", None, None, "uncategorized"),
    ])
    books.purchase(date(2026, 8, 4), "25.00")

    uncategorized = _row(session, books).uncategorized

    assert [(u.supplier_name, u.amount) for u in uncategorized] == [
        ("Shop ApS", Decimal("40.00")), (None, Decimal("25.00")),
    ]
    assert uncategorized[0].invoice_id == invoice.id
    assert uncategorized[0].voucher_id is not None


def test_each_list_holds_at_most_five(session):
    books = Books(session)
    for index in range(8):
        books.purchase(date(2026, 8, 3), f"{index + 1}0.00", vendor=books.supplier(f"New {index} ApS"))

    row = _row(session, books)

    assert len(row.new_suppliers) == 5
    assert len(row.uncategorized) == 5
    assert row.new_suppliers[0].name == "New 7 ApS"
