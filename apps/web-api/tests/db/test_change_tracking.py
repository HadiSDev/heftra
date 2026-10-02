"""`changed_at` moves when what a line or invoice says changes, and only then."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import update
from sqlmodel import Session

from web_api.db.models import Invoice, InvoiceLine, Vendor

LONG_AGO = datetime(2020, 1, 1, tzinfo=timezone.utc)


def _age(session: Session, row) -> None:
    row.changed_at = LONG_AGO
    session.add(row)
    session.commit()


def _moved(session: Session, row) -> bool:
    session.refresh(row)
    return row.changed_at.replace(tzinfo=timezone.utc) > LONG_AGO


def test_a_new_category_is_a_change(engine, seed):
    with Session(engine) as s:
        line = s.get(InvoiceLine, seed["line_a1"])
        _age(s, line)
        line.spend_category_id = "another-category"
        s.add(line)
        s.commit()
        assert _moved(s, line)


def test_an_emission_sector_is_not(engine, seed):
    with Session(engine) as s:
        line = s.get(InvoiceLine, seed["line_a1"])
        _age(s, line)
        line.emission_sector_id = "a-sector"
        line.rationale = "matched"
        s.add(line)
        s.commit()
        assert not _moved(s, line)


def test_a_bulk_update_of_other_fields_leaves_it(engine, seed):
    with Session(engine) as s:
        line = s.get(InvoiceLine, seed["line_a1"])
        _age(s, line)
        s.exec(update(InvoiceLine).where(InvoiceLine.id == line.id)
               .values(emission_sector_id=None))
        s.commit()
        assert not _moved(s, line)


def test_a_new_supplier_on_the_invoice_is_a_change(engine, seed):
    with Session(engine) as s:
        invoice = s.get(Invoice, s.get(InvoiceLine, seed["line_a1"]).invoice_id)
        _age(s, invoice)
        vendor = Vendor(name="Proshop A/S")
        s.add(vendor)
        s.commit()
        invoice.vendor_id = vendor.id
        s.add(invoice)
        s.commit()
        assert _moved(s, invoice)


def test_setting_the_same_value_is_not_a_change(engine, seed):
    with Session(engine) as s:
        line = s.get(InvoiceLine, seed["line_a1"])
        _age(s, line)
        line.description = line.description
        line.status = "verified"
        s.add(line)
        s.commit()
        assert not _moved(s, line)
