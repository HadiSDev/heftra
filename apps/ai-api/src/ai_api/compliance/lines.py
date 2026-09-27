"""The company's invoice lines as analysis reads them."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlmodel import Session, col, select

from web_api.db.models import Invoice, InvoiceLine, Vendor
from web_api.vat import international_vat


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

    @property
    def text(self) -> str:
        """What the line says, for similarity and for the judge."""
        parts = [self.item_name, self.description, " / ".join(self.category_path)]
        return " — ".join(part for part in parts if part)

    @property
    def question_key(self) -> str:
        """A digest of what decides whether this line falls under a term."""
        payload = json.dumps([_norm(self.item_name), _norm(self.description), _norm(self.unit),
                              [_norm(level) for level in self.category_path],
                              _norm(self.vendor_name)])
        return hashlib.sha256(payload.encode()).hexdigest()


def load_lines(session: Session, company_id: str, start: date,
               end: date | None) -> list[AnalysedLine]:
    """The company's positive lines invoiced from `start` to `end` (open-ended without one)."""
    conditions = [InvoiceLine.company_id == company_id, Invoice.invoice_date >= start]
    if end is not None:
        conditions.append(Invoice.invoice_date <= end)
    rows = session.exec(
        select(InvoiceLine, Invoice.invoice_date, Invoice.currency, Invoice.vendor_id,
               Vendor.name, Vendor.vat_number, Vendor.country_code)
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .outerjoin(Vendor, Vendor.id == Invoice.vendor_id)
        .where(*conditions)
        .order_by(col(Invoice.invoice_date), col(InvoiceLine.id))
    ).all()
    lines = []
    for line, spent_on, currency, vendor_id, vendor_name, vat, country in rows:
        base = line.base_amount if line.base_amount is not None else line.amount
        if base is None or base <= 0:
            continue
        lines.append(AnalysedLine(
            line_id=line.id, invoice_id=line.invoice_id, vendor_id=vendor_id,
            vendor_name=vendor_name, vendor_vat=international_vat(vat, country),
            item_name=line.item_name, description=line.description, quantity=line.quantity,
            unit=line.unit, unit_price=line.unit_price, amount=line.amount,
            discount=line.discount, base_amount=base, currency=currency, spent_on=spent_on,
            category_id=line.spend_category_id,
            category_path=tuple(level for level in (line.level_1, line.level_2, line.level_3,
                                                    line.level_4) if level),
        ))
    return lines


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


def _norm(value: str | None) -> str:
    return " ".join((value or "").lower().split())
