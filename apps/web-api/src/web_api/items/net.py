"""Line amounts without VAT, in the base currency, decided by the invoice's own arithmetic.

A document's lines may show their amounts with VAT. A line that prints a net figure
(`subtotal`) below its amount, by no more than a VAT rate could explain, says so itself.
Otherwise the invoice's totals decide: its lines include VAT only when they add up to a total
with VAT, from the document or the ledger, and to no total without it. Then each line is
scaled by the invoice's share without VAT, if that share is one a VAT rate gives. When the
totals settle neither, the amounts are kept as they are."""
from __future__ import annotations

from sqlalchemy import Subquery, and_, case, func, or_
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import col, select

from .. import config
from ..db.models import Invoice, InvoiceLine

MAX_VAT_RATE = 0.27


def invoice_net_shares() -> Subquery:
    """Each invoice's `share` of its line amounts that is not VAT: below 1 when its lines
    include VAT, else 1."""
    lines = (select(InvoiceLine.invoice_id, func.sum(InvoiceLine.amount).label("lines_total"))
             .group_by(InvoiceLine.invoice_id).subquery())
    lines_total = lines.c.lines_total
    ledger_net = case((col(Invoice.tax) > 0, Invoice.total - Invoice.tax))
    adds_up_to_gross = or_(_near(lines_total, col(Invoice.document_total)),
                           _near(lines_total, col(Invoice.total)))
    adds_up_to_net = or_(_near(lines_total, col(Invoice.document_subtotal)),
                         _near(lines_total, ledger_net))
    share = func.coalesce(Invoice.document_subtotal / Invoice.document_total,
                          ledger_net / Invoice.total)
    includes_vat = and_(adds_up_to_gross, ~adds_up_to_net,
                        share >= 1 / (1 + MAX_VAT_RATE), share < 1)
    return (select(Invoice.id.label("invoice_id"),
                   case((includes_vat, share), else_=1).label("share"))
            .join(lines, lines.c.invoice_id == Invoice.id)
            .subquery())


def net_base_amount(shares: Subquery) -> ColumnElement:
    """A line's base amount without VAT; the query joins `shares` on the line's invoice."""
    subtotal, amount = col(InvoiceLine.subtotal), col(InvoiceLine.amount)
    printed_net = and_(subtotal > 0, subtotal < amount, amount <= subtotal * (1 + MAX_VAT_RATE))
    return case(
        (printed_net, InvoiceLine.base_amount * subtotal / amount),
        else_=InvoiceLine.base_amount * func.coalesce(shares.c.share, 1),
    )


def _near(lines_total, target) -> ColumnElement:
    """The lines add up to `target` within the ledger's reconciliation tolerance."""
    relative = func.abs(target) * config.DOC_RECONCILE_TOLERANCE_PCT
    tolerance = case((relative > config.DOC_RECONCILE_TOLERANCE_ABS, relative),
                     else_=config.DOC_RECONCILE_TOLERANCE_ABS)
    return and_(target.is_not(None), func.abs(lines_total - target) <= tolerance)
