"""A company's lines grouped into items in the database."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from agreement_books import Books
from ai_api.items.grouping import company_items
from ai_api.items.refresh import refresh_item_keys


def test_repeated_purchases_are_one_item_and_suppliers_are_kept_apart(engine):
    with Session(engine) as s:
        books = Books(s)
        tree = books.tree("Office Equipment")
        for day in (1, 2, 3):
            books.line(books.atea, "Magic Keyboard", unit_price="1000",
                       on=date(2026, 3, day), category=tree["Office Equipment"])
        books.line(books.proshop, "Magic Keyboard", unit_price="1100",
                   category=tree["Office Equipment"])
        refresh_item_keys(s, books.company.id, None)

        items = company_items(s, books.company.id)

        assert [(item.vendor_name, item.lines, item.spend) for item in items] == [
            ("Atea A/S", 3, Decimal("3000")), ("Proshop A/S", 1, Decimal("1100"))]
        atea = items[0]
        assert (atea.first_on, atea.last_on) == (date(2026, 3, 1), date(2026, 3, 3))
        assert atea.category_path == ("Office Equipment",)


def test_items_are_filtered_by_dates_categories_and_keys(engine):
    with Session(engine) as s:
        books = Books(s)
        tree = books.tree("Office Equipment", "Coffee")
        books.line(books.atea, "Magic Keyboard", unit_price="1000", on=date(2025, 6, 1),
                   category=tree["Office Equipment"])
        books.line(books.atea, "Dell laptop", unit_price="9000", on=date(2026, 3, 1),
                   category=tree["Office Equipment"])
        books.line(books.atea, "Espresso", unit_price="100", on=date(2026, 3, 1),
                   category=tree["Coffee"])
        refresh_item_keys(s, books.company.id, None)

        recent = company_items(s, books.company.id, start=date(2026, 1, 1),
                               category_ids=[tree["Office Equipment"].id])
        by_key = company_items(s, books.company.id, keys=[recent[0].key])

        assert [item.item_name for item in recent] == ["Dell laptop"]
        assert [item.key for item in by_key] == [recent[0].key]
