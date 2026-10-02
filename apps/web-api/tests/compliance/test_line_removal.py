"""A line with findings against it can still be removed, and its month is checked again."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from agreement_records import agreement, finding, supplier, term
from web_api.agreements.line_removal import remove_line
from web_api.db.models import AgreementFinding, Invoice, InvoiceLine

LONG_AGO = datetime(2020, 1, 1, tzinfo=timezone.utc)


def test_a_line_with_a_finding_is_removed_with_it(engine, seed):
    with Session(engine) as s:
        record = agreement(s, seed["comp_a"], vendor=supplier(s))
        finding(s, agreement=record, term=term(s, record.id), line_id=seed["line_a1"],
                invoice_id=seed["inv_a"])
        invoice = s.get(Invoice, seed["inv_a"])
        invoice.changed_at = LONG_AGO
        s.add(invoice)
        s.commit()

        remove_line(s, s.get(InvoiceLine, seed["line_a1"]))
        s.commit()

        assert s.get(InvoiceLine, seed["line_a1"]) is None
        assert s.exec(select(AgreementFinding)).all() == []
        assert s.get(Invoice, seed["inv_a"]).changed_at.replace(tzinfo=timezone.utc) > LONG_AGO
