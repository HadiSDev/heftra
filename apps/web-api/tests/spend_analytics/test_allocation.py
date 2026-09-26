"""Spend is what the ERP posted to expense, split across categories and suppliers by the lines."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from spend_books import Books
from web_api.spend_analytics.allocation import allocate
from web_api.spend_analytics.periods import Period

SEPTEMBER = Period(date(2026, 9, 1), date(2026, 9, 30))


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _parts(allocation) -> dict[tuple[str | None, str | None], Decimal]:
    parts: dict[tuple[str | None, str | None], Decimal] = {}
    for row in allocation.spend:
        key = (row.category, row.subcategory)
        parts[key] = parts.get(key, Decimal("0")) + row.amount
    return parts


def test_lines_printed_with_vat_are_attributed_the_posted_net(session):
    books = Books(session)
    hiper = books.supplier("Hiper A/S")
    books.purchase(date(2026, 9, 3), "295.20", vat="73.80", vendor=hiper,
                   lines=[("369.00", "Technology", "Internet", "ai_categorized")])

    allocation = allocate(session, [books.company.id], SEPTEMBER)

    (row,) = allocation.spend
    assert row.amount == Decimal("295.20")
    assert (row.category, row.subcategory, row.categorized) == ("Technology", "Internet", True)
    assert row.vendor_id == hiper.id
    assert row.currency == "DKK"


def test_a_voucher_is_split_across_its_categories_and_adds_up_exactly(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "430.46", vendor=books.supplier("Compumail"), lines=[
        ("484.00", "Technology", "Hardware", "verified"),
        ("39.00", "Logistics", "Freight", "uncategorized"),
        ("15.07", "Financial Services", "Fees", "ai_categorized"),
    ])

    parts = _parts(allocate(session, [books.company.id], SEPTEMBER))

    assert parts == {
        ("Technology", "Hardware"): Decimal("387.20"),
        (None, None): Decimal("31.20"),
        ("Financial Services", "Fees"): Decimal("12.06"),
    }
    assert sum(parts.values()) == Decimal("430.46")


def test_rounding_leaves_no_cent_behind(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "100.00", vendor=books.supplier("Thirds ApS"), lines=[
        ("1", "A", "a", "verified"), ("1", "B", "b", "verified"), ("1", "C", "c", "verified"),
    ])

    parts = _parts(allocate(session, [books.company.id], SEPTEMBER))

    assert sum(parts.values()) == Decimal("100.00")
    assert sorted(parts.values()) == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]


def test_failed_and_missing_lines_are_not_categorized(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "100.00", vendor=books.supplier("Doubt ApS"), lines=[
        ("50", "Technology", "Software", "ai_failed"),
        ("50", None, None, "uncategorized"),
    ])
    books.purchase(date(2026, 9, 4), "40.00", vendor=books.supplier("No Lines ApS"))

    allocation = allocate(session, [books.company.id], SEPTEMBER)

    assert _parts(allocation) == {(None, None): Decimal("140.00")}
    assert all(not row.categorized for row in allocation.spend)


def test_a_posting_without_an_invoice_counts_with_no_supplier(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "25.00")

    (row,) = allocate(session, [books.company.id], SEPTEMBER).spend

    assert row.amount == Decimal("25.00")
    assert row.vendor_id is None
    assert row.invoice_id is None
    assert row.categorized is False


def test_an_unconverted_voucher_is_counted_not_summed(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "25.00", converted=False)

    allocation = allocate(session, [books.company.id], SEPTEMBER)

    assert allocation.spend == []
    assert len(allocation.unconverted) == 1
    assert allocation.unconverted[0].currency == "DKK"


def test_only_the_window_and_the_callers_companies_are_read(session):
    ours = Books(session)
    theirs = Books(session, name="Other A/S")
    ours.purchase(date(2026, 9, 3), "10.00")
    ours.purchase(date(2026, 8, 31), "20.00")
    theirs.purchase(date(2026, 9, 3), "30.00")

    allocation = allocate(session, [ours.company.id], SEPTEMBER)

    assert [row.amount for row in allocation.spend] == [Decimal("10.00")]
    assert allocation.spend[0].spent_on == date(2026, 9, 3)


def test_each_company_is_in_its_own_base_currency(session):
    danish = Books(session)
    swedish = Books(session, name="Acme AB", currency="SEK", organization_id=danish.organization_id)
    danish.purchase(date(2026, 9, 3), "10.00")
    swedish.purchase(date(2026, 9, 3), "30.00")

    allocation = allocate(session, [danish.company.id, swedish.company.id], SEPTEMBER)

    assert sorted((row.currency, row.amount) for row in allocation.spend) == [
        ("DKK", Decimal("10.00")), ("SEK", Decimal("30.00")),
    ]


def test_no_companies_read_nothing(session):
    assert allocate(session, [], SEPTEMBER).spend == []


def test_an_uncategorized_discount_is_absorbed_by_what_it_discounts(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "46.40", vendor=books.supplier("DSB"), lines=[
        ("58.00", "Travel & Entertainment", "Ground Transport", "ai_categorized"),
        ("-11.60", None, None, "uncategorized"),
    ])

    parts = _parts(allocate(session, [books.company.id], SEPTEMBER))

    assert parts == {("Travel & Entertainment", "Ground Transport"): Decimal("46.40")}


def test_the_category_is_the_second_tree_level_not_the_direct_indirect_split(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "10.00", vendor=books.supplier("Shop ApS"),
                   lines=[("10", "Technology", "Software", "verified")])

    (row,) = allocate(session, [books.company.id], SEPTEMBER).spend

    assert (row.category, row.subcategory) == ("Technology", "Software")
