"""The tiles: the period's spend and its comparison, the categorized share, suppliers and work waiting."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from spend_books import Books
from web_api.spend_analytics.overview import spend_overview
from web_api.spend_analytics.periods import Period

Q3 = Period(date(2026, 7, 1), date(2026, 9, 30))


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _row(overview, currency: str = "DKK"):
    return next(row for row in overview.rows if row.currency == currency)


def test_the_period_is_compared_with_the_one_before(session):
    books = Books(session)
    books.purchase(date(2026, 8, 3), "12000.00")
    books.purchase(date(2026, 5, 3), "10000.00")

    overview = spend_overview(session, [books.company.id], Q3)

    assert _row(overview).spend == Decimal("12000.00")
    assert _row(overview).comparison_spend == Decimal("10000.00")
    assert overview.comparison.start == date(2026, 4, 1)


def test_the_categorized_share_is_the_part_of_the_spend_with_a_category(session):
    books = Books(session)
    books.purchase(date(2026, 8, 3), "80.00", vendor=books.supplier("Split ApS"), lines=[
        ("75", "Technology", "Software", "verified"), ("25", None, None, "uncategorized"),
    ])

    assert _row(spend_overview(session, [books.company.id], Q3)).categorized_spend == Decimal("60.00")


def test_twelve_months_end_with_the_period_and_quiet_ones_are_zero(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "30.00")
    books.purchase(date(2025, 11, 3), "20.00")

    months = _row(spend_overview(session, [books.company.id], Q3)).months

    assert [m.month for m in months][0] == date(2025, 10, 1)
    assert [m.month for m in months][-1] == date(2026, 9, 1)
    assert {m.month: m.amount for m in months}[date(2025, 11, 1)] == Decimal("20.00")
    assert {m.month: m.amount for m in months}[date(2026, 3, 1)] == Decimal("0")


def test_a_supplier_first_invoiced_in_the_period_is_new(session):
    books = Books(session)
    old, fresh = books.supplier("Old ApS"), books.supplier("Fresh ApS")
    books.purchase(date(2025, 2, 1), "10.00", vendor=old)
    books.purchase(date(2026, 8, 1), "10.00", vendor=old)
    books.purchase(date(2026, 8, 2), "10.00", vendor=fresh)

    row = _row(spend_overview(session, [books.company.id], Q3))

    assert row.active_suppliers == 2
    assert row.new_suppliers == 1


def test_unconverted_vouchers_are_counted(session):
    books = Books(session)
    books.purchase(date(2026, 8, 3), "5.00")
    books.purchase(date(2026, 8, 4), "5.00", converted=False)

    assert _row(spend_overview(session, [books.company.id], Q3)).unconverted_vouchers == 1


def test_work_waiting_is_counted_whatever_the_period(session):
    books = Books(session)
    doubtful = books.purchase(date(2025, 1, 5), "10.00", vendor=books.supplier("Doubt ApS"),
                              lines=[("10", "Technology", "Software", "ai_categorized")])
    for line in doubtful.lines:
        line.confidence = Decimal("0.3")
    failed = books.purchase(date(2026, 8, 3), "10.00", vendor=books.supplier("Scan ApS"))
    failed.doc_status = "failed"
    wrong = books.purchase(date(2026, 8, 4), "10.00", vendor=books.supplier("Total ApS"))
    wrong.total, wrong.tax, wrong.document_total = Decimal("12.50"), Decimal("2.50"), Decimal("99.00")
    session.add_all([doubtful, failed, wrong])
    session.commit()

    attention = spend_overview(session, [books.company.id], Q3).attention

    assert (attention.needs_review_lines, attention.failed_documents, attention.totals_mismatch) == (1, 1, 1)


def test_each_currency_is_its_own_row(session):
    danish = Books(session)
    swedish = Books(session, name="Acme AB", currency="SEK", organization_id=danish.organization_id)
    danish.purchase(date(2026, 8, 3), "10.00")
    swedish.purchase(date(2026, 8, 3), "30.00")

    overview = spend_overview(session, [danish.company.id, swedish.company.id], Q3)

    assert [(row.currency, row.spend) for row in overview.rows] == [
        ("DKK", Decimal("10.00")), ("SEK", Decimal("30.00")),
    ]


def test_no_spend_gives_no_rows(session):
    books = Books(session)

    assert spend_overview(session, [books.company.id], Q3).rows == []
