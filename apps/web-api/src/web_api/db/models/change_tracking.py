"""Stamping `changed_at` on lines and invoices when something an agreement check reads changes."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import event, inspect

from .invoice import Invoice
from .invoice_line import InvoiceLine

LINE_FIELDS = ("invoice_id", "item_name", "description", "unit", "quantity", "unit_price",
               "amount", "discount", "base_amount", "base_currency", "spend_category_id")
INVOICE_FIELDS = ("vendor_id", "invoice_date", "currency", "base_currency")


def _stamp_when_changed(fields: tuple[str, ...]):
    def stamp(mapper, connection, target) -> None:
        attributes = inspect(target).attrs
        if any(attributes[field].history.has_changes() for field in fields):
            target.changed_at = datetime.now(timezone.utc)
    return stamp


event.listen(InvoiceLine, "before_update", _stamp_when_changed(LINE_FIELDS))
event.listen(Invoice, "before_update", _stamp_when_changed(INVOICE_FIELDS))
