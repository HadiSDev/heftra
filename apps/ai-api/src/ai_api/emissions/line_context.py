"""What a matcher is told about a line, and what it can look up about its supplier and invoice."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import NamedTuple

from sqlmodel import Session, select

from web_api.db.models import Invoice, InvoiceLine, Vendor

OTHER_LINES_SHOWN = 10


class LineContext(NamedTuple):
    line_id: str
    item_name: str | None
    description: str | None
    amount: Decimal | None
    currency: str | None
    category_path: list[str]
    supplier_name: str | None
    supplier_country: str | None
    supplier_description: str | None
    supplier_website: str | None
    other_lines: list[str]

    @property
    def question_key(self) -> str:
        """A digest of what makes this line the matching question it is."""
        payload = json.dumps([
            _norm(self.item_name), _norm(self.description),
            [_norm(level) for level in self.category_path],
            _norm(self.supplier_name), _norm(self.supplier_country),
        ])
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def sample(self) -> str:
        """A readable trace of the question, for whoever inspects the cache."""
        parts = [part for part in (self.item_name or self.description, self.supplier_name) if part]
        return " | ".join(parts)[:200]


def line_contexts(session: Session, lines: list[InvoiceLine]) -> list[LineContext]:
    """Each line's context, loading its invoices, suppliers and sibling lines in batches."""
    invoice_ids = {line.invoice_id for line in lines}
    if not invoice_ids:
        return []
    invoices = {
        invoice.id: invoice
        for invoice in session.exec(
            select(Invoice).where(Invoice.id.in_(invoice_ids))  # type: ignore[attr-defined]
        ).all()
    }
    vendor_ids = {invoice.vendor_id for invoice in invoices.values() if invoice.vendor_id}
    vendors = {
        vendor.id: vendor
        for vendor in session.exec(
            select(Vendor).where(Vendor.id.in_(vendor_ids))  # type: ignore[attr-defined]
        ).all()
    } if vendor_ids else {}
    siblings: dict[str, list[tuple[str, str]]] = {}
    for invoice_id, line_id, name, description in session.exec(
        select(InvoiceLine.invoice_id, InvoiceLine.id, InvoiceLine.item_name,
               InvoiceLine.description)
        .where(InvoiceLine.invoice_id.in_(invoice_ids))  # type: ignore[attr-defined]
        .order_by(InvoiceLine.invoice_id, InvoiceLine.sequence)
    ).all():
        label = name or description
        if label:
            siblings.setdefault(invoice_id, []).append((line_id, label))

    contexts = []
    for line in lines:
        invoice = invoices[line.invoice_id]
        vendor = vendors.get(invoice.vendor_id) if invoice.vendor_id else None
        contexts.append(LineContext(
            line_id=line.id,
            item_name=line.item_name,
            description=line.description,
            amount=line.amount,
            currency=invoice.currency,
            category_path=[level for level in (line.level_1, line.level_2, line.level_3,
                                               line.level_4) if level],
            supplier_name=vendor.name if vendor else None,
            supplier_country=(vendor.country_code if vendor else None)
            or invoice.document_supplier_country_code,
            supplier_description=vendor.description if vendor else None,
            supplier_website=(vendor.website if vendor else None)
            or invoice.document_supplier_website,
            other_lines=[label for line_id, label in siblings.get(line.invoice_id, [])
                         if line_id != line.id][:OTHER_LINES_SHOWN],
        ))
    return contexts


def _norm(value: str | None) -> str:
    return " ".join((value or "").lower().split())
