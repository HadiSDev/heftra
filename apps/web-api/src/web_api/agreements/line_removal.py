"""Removing an invoice line that agreement analysis may have read."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete
from sqlmodel import Session

from ..db.models import AgreementFinding, Invoice, InvoiceLine


def remove_line(session: Session, line: InvoiceLine) -> None:
    """Delete the line and its findings, and mark its invoice changed, so the next analysis
    recalculates that month's spend without it."""
    session.exec(delete(AgreementFinding).where(AgreementFinding.invoice_line_id == line.id))
    invoice = session.get(Invoice, line.invoice_id)
    if invoice is not None:
        invoice.changed_at = datetime.now(timezone.utc)
        session.add(invoice)
    session.delete(line)
