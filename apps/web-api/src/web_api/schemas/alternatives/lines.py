"""A spend line an item was bought on."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ItemLineRead(BaseModel):
    """`voucher_id` is the ERP voucher the invoice was posted on, to open the line in Spend
    Lines; none until the invoice is posted. `net_amount` is `base_amount` without VAT, as
    the item's figures count it."""

    id: str
    invoice_id: str
    voucher_id: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    item_name: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    base_amount: Decimal | None = None
    net_amount: Decimal | None = None
    base_currency: str | None = None
