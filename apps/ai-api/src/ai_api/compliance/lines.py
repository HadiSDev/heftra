"""The company's invoice lines as analysis reads them."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlmodel import Session, col, select

from web_api.db.models import InvoiceLine


@dataclass(frozen=True)
class AnalysedLine:
    line_id: str
    invoice_id: str
    vendor_id: str | None
    vendor_name: str | None
    vendor_vat: str | None
    item_name: str | None
    description: str | None
    quantity: Decimal | None
    unit: str | None
    unit_price: Decimal | None
    amount: Decimal | None
    discount: Decimal | None
    base_amount: Decimal
    currency: str | None
    spent_on: date | None
    category_id: str | None
    category_path: tuple[str, ...]


def invoice_discount_rates(session: Session, invoice_ids: set[str]) -> dict[str, Decimal]:
    """Each invoice's discount lines as a share of its other lines, where it has any."""
    if not invoice_ids:
        return {}
    positive: dict[str, Decimal] = {}
    negative: dict[str, Decimal] = {}
    for invoice_id, amount in session.exec(
        select(InvoiceLine.invoice_id, InvoiceLine.amount)
        .where(col(InvoiceLine.invoice_id).in_(invoice_ids), col(InvoiceLine.amount).is_not(None))
    ).all():
        if amount >= 0:
            positive[invoice_id] = positive.get(invoice_id, Decimal(0)) + amount
        else:
            negative[invoice_id] = negative.get(invoice_id, Decimal(0)) - amount
    return {invoice_id: discount / positive[invoice_id]
            for invoice_id, discount in negative.items() if positive.get(invoice_id)}
