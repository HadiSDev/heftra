"""A fictional supplier of the demo company, how often it invoices and what it sells."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .offer import OfferSpec


class Billing(str, Enum):
    """Orders come as they are placed; a monthly supplier bills every offer once a month."""

    ORDERS = "orders"
    MONTHLY = "monthly"


@dataclass(frozen=True)
class SupplierSpec:
    """`account` is the ERP expense account its invoices post to. `vat_number` is fictional:
    its digits fail the Danish CVR checksum, so it can't be a real company's."""

    key: str
    name: str
    vat_number: str
    city: str
    website: str
    description: str
    account: str
    invoice_prefix: str
    offers: tuple[OfferSpec, ...]
    invoices_per_month: float = 1.0
    lines_per_invoice: tuple[int, int] = (1, 3)
    seasonal: bool = True
    billing: Billing = Billing.ORDERS
    first_day: date | None = None
