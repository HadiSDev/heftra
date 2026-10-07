"""Render an invoice as a PDF document."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from .invoices import VoucherInvoice

PAYMENT_DAYS = 30

_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    autoescape=select_autoescape(["html"]),
)


def _money(value: Decimal) -> str:
    return f"{value:,.2f}"


def _quantity(value: Decimal) -> str:
    return f"{value.normalize():f}"


_env.filters["money"] = _money
_env.filters["quantity"] = _quantity


def invoice_pdf(invoice: VoucherInvoice) -> bytes:
    """The invoice as the supplier would have sent it."""
    html = _env.get_template("invoice.html").render(
        invoice=invoice, due=invoice.issued + timedelta(days=PAYMENT_DAYS),
        payment_days=PAYMENT_DAYS,
    )
    return HTML(string=html).write_pdf()
