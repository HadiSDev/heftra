"""The invoice behind an ERP voucher, read from the demo database."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import psycopg2

from . import settings

INVOICE_SQL = """
select i.id, i.invoice_number, i.invoice_date, i.currency, i.total, i.tax,
       coalesce(v.name, i.supplier_name), coalesce(v.vat_number, i.supplier_vat_number),
       v.website, c.name, c.vat_number, c.website
from erp_entries e
join invoices i on i.id = e.source_invoice_id
join companies c on c.id = i.company_id
left join vendors v on v.id = i.vendor_id
where e.voucher_id = %s
order by e.id
limit 1
"""

LINES_SQL = """
select item_name, description, quantity, unit, unit_price, discount, amount
from invoice_lines
where invoice_id = %s
order by sequence
"""


@dataclass(frozen=True)
class Party:
    name: str
    vat_number: str | None
    website: str | None


@dataclass(frozen=True)
class Line:
    item: str
    description: str | None
    quantity: Decimal
    unit: str | None
    unit_price: Decimal
    discount: Decimal | None
    amount: Decimal


@dataclass(frozen=True)
class VoucherInvoice:
    voucher_id: str
    number: str
    issued: date
    currency: str
    supplier: Party
    buyer: Party
    lines: list[Line]
    tax: Decimal
    total: Decimal

    @property
    def subtotal(self) -> Decimal:
        return self.total - self.tax


def find(voucher_id: str) -> VoucherInvoice | None:
    """The invoice posted under this voucher, or None if there is none."""
    with psycopg2.connect(settings.DATABASE_URL) as connection, connection.cursor() as cursor:
        cursor.execute(INVOICE_SQL, (voucher_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        cursor.execute(LINES_SQL, (row[0],))
        lines = [Line(*line) for line in cursor.fetchall()]
    return VoucherInvoice(
        voucher_id=voucher_id, number=row[1], issued=row[2], currency=row[3], total=row[4],
        tax=row[5], supplier=Party(row[6], row[7], row[8]), buyer=Party(row[9], row[10], row[11]),
        lines=lines,
    )
