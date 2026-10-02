"""The stored item a spend line bought, keyed and created when the line is first asked about."""
from __future__ import annotations

from sqlmodel import Session, select

from ..db.models import CompanyItem, Invoice, InvoiceLine
from .keys import item_key


def line_item(session: Session, line: InvoiceLine) -> CompanyItem | None:
    """The stored item of the line, or None when there is none yet."""
    if line.item_key is None:
        return None
    return session.exec(select(CompanyItem).where(
        CompanyItem.company_id == line.company_id,
        CompanyItem.item_key == line.item_key)).first()


def ensure_line_item(session: Session, line: InvoiceLine) -> CompanyItem:
    """The line's stored item, keying the line and storing the item from it when needed; the
    worker fills in its figures when it searches it. The caller commits."""
    invoice = session.get(Invoice, line.invoice_id)
    if line.item_key is None:
        line.item_key = item_key(line.item_name, line.description, line.unit,
                                 line.spend_category_id, invoice.vendor_id if invoice else None)
        session.add(line)
    item = line_item(session, line)
    if item is None:
        item = CompanyItem(company_id=line.company_id, item_key=line.item_key,
                           item_name=line.item_name, description=line.description,
                           unit=line.unit, vendor_id=invoice.vendor_id if invoice else None,
                           category_id=line.spend_category_id, base_currency=line.base_currency)
        session.add(item)
        session.flush()
    return item
