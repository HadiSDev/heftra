"""The ERP voucher each invoice was posted on."""
from __future__ import annotations

from sqlmodel import Session, col, select

from ..db.models import ErpEntry


def voucher_ids(session: Session, invoice_ids: set[str]) -> dict[str, str]:
    """Each posted invoice's voucher id; invoices not posted yet are left out."""
    if not invoice_ids:
        return {}
    rows = session.exec(
        select(ErpEntry.source_invoice_id, ErpEntry.voucher_id)
        .where(col(ErpEntry.source_invoice_id).in_(invoice_ids),
               col(ErpEntry.voucher_id).is_not(None))
    ).all()
    return {invoice_id: voucher_id for invoice_id, voucher_id in rows if invoice_id}
