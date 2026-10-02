"""Lines get their item key, and only changed lines are keyed again."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from agreement_books import Books
from web_api.items.keys import item_key
from ai_api.items.refresh import refresh_item_keys
from web_api.db.models import Invoice, InvoiceLine

LONG_AGO = datetime(2020, 1, 1, tzinfo=timezone.utc)


def _age_everything(session: Session) -> None:
    for row in [*session.exec(select(InvoiceLine)).all(), *session.exec(select(Invoice)).all()]:
        row.changed_at = LONG_AGO
        session.add(row)
    session.commit()


def test_every_line_without_a_key_is_keyed_page_by_page(engine):
    with Session(engine) as s:
        books = Books(s)
        lines = [books.line(books.proshop, f"Laptop {n}", unit_price="9000") for n in range(5)]

        assert refresh_item_keys(s, books.company.id, None, page_size=2) == 5

        line = s.get(InvoiceLine, lines[0].id)
        invoice = s.get(Invoice, line.invoice_id)
        assert line.item_key == item_key("Laptop 0", None, "unit", None, invoice.vendor_id)


def test_only_lines_changed_since_are_keyed_again(engine):
    with Session(engine) as s:
        books = Books(s)
        kept = books.line(books.proshop, "Dell laptop", unit_price="9000")
        moved = books.line(books.proshop, "HP laptop", unit_price="7000")
        refresh_item_keys(s, books.company.id, None)
        _age_everything(s)
        since = datetime.now(timezone.utc) - timedelta(minutes=1)

        line = s.get(InvoiceLine, moved.id)
        line.item_name = "HP EliteBook laptop"
        s.add(line)
        s.commit()

        assert refresh_item_keys(s, books.company.id, since) == 1
        assert s.get(InvoiceLine, kept.id).item_key is not None


def test_a_new_supplier_on_the_invoice_rekeys_its_lines(engine):
    with Session(engine) as s:
        books = Books(s)
        line = books.line(books.proshop, "Dell laptop", unit_price="9000")
        refresh_item_keys(s, books.company.id, None)
        before = s.get(InvoiceLine, line.id).item_key
        _age_everything(s)
        since = datetime.now(timezone.utc) - timedelta(minutes=1)

        invoice = s.get(Invoice, line.invoice_id)
        invoice.vendor_id = books.atea.id
        s.add(invoice)
        s.commit()

        assert refresh_item_keys(s, books.company.id, since) == 1
        assert s.get(InvoiceLine, line.id).item_key != before
