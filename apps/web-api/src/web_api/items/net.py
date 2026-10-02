"""Line amounts without VAT, in the base currency.

A document's lines may show their amounts with VAT. A line that also prints a net figure
(`subtotal`) below its amount says so itself; one equal to the amount says nothing. Otherwise
the invoice's totals tell: when its lines add up to the total with VAT rather than without,
each line is scaled by the invoice's share without VAT."""
from __future__ import annotations

from sqlalchemy import Subquery, and_, case, func
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col, select

from ..db.models import Invoice, InvoiceLine


def invoice_net_shares() -> Subquery:
    """Each invoice's `share` of its line amounts that is not VAT: below 1 when its lines
    include VAT, else 1."""
    lines = (select(InvoiceLine.invoice_id, func.sum(InvoiceLine.amount).label("lines_total"))
             .group_by(InvoiceLine.invoice_id).subquery())
    gross = func.coalesce(Invoice.document_total, Invoice.total)
    net = func.coalesce(Invoice.document_subtotal, Invoice.total - func.coalesce(Invoice.tax, 0))
    includes_vat = and_(gross > net, net > 0,
                        func.abs(lines.c.lines_total - gross) < func.abs(lines.c.lines_total - net))
    return (select(Invoice.id.label("invoice_id"),
                   case((includes_vat, net / gross), else_=1).label("share"))
            .join(lines, lines.c.invoice_id == Invoice.id)
            .subquery())


def net_base_amount(shares: Subquery) -> ColumnElement:
    """A line's base amount without VAT; the query joins `shares` on the line's invoice."""
    printed_net = and_(col(InvoiceLine.subtotal) > 0,
                       col(InvoiceLine.subtotal) < col(InvoiceLine.amount))
    return case(
        (printed_net, InvoiceLine.base_amount * InvoiceLine.subtotal / InvoiceLine.amount),
        else_=InvoiceLine.base_amount * func.coalesce(shares.c.share, 1),
    )
