"""The spend lines an item was bought on in its window, newest first."""
from __future__ import annotations

from datetime import date, timedelta

from sqlmodel import Session, col, select

from ..db.models import CompanyItem, Invoice, InvoiceLine
from ..items.window import WINDOW_DAYS
from ..schemas.alternatives import ItemLineRead
from ..vouchers.invoices import voucher_ids

MAX_LINES = 100


def item_lines(session: Session, item: CompanyItem, *,
               today: date | None = None) -> list[ItemLineRead]:
    """The lines behind the item's figures: same company and item, bought with a positive
    amount within the last `WINDOW_DAYS`."""
    since = (today or date.today()) - timedelta(days=WINDOW_DAYS)
    rows = session.exec(
        select(InvoiceLine, Invoice)
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .where(InvoiceLine.company_id == item.company_id,
               InvoiceLine.item_key == item.item_key,
               col(InvoiceLine.base_amount) > 0,
               Invoice.invoice_date >= since)
        .order_by(col(Invoice.invoice_date).desc(), col(InvoiceLine.id))
        .limit(MAX_LINES)
    ).all()
    vouchers = voucher_ids(session, {invoice.id for _, invoice in rows})
    return [
        ItemLineRead(
            id=line.id, invoice_id=invoice.id, voucher_id=vouchers.get(invoice.id),
            invoice_number=invoice.invoice_number or invoice.document_invoice_number,
            invoice_date=invoice.invoice_date, item_name=line.item_name or line.description,
            quantity=line.quantity, unit=line.unit, base_amount=line.base_amount,
            base_currency=line.base_currency)
        for line, invoice in rows
    ]
