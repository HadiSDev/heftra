"""The planned lines a term covers: its products, bought while the agreement runs."""
from __future__ import annotations

from dataclasses import dataclass

from ...catalog.shapes import AgreementSpec, TermSpec
from ...generation.planned import PlannedInvoice, PlannedLine
from ...settings import LAST_DAY


@dataclass(frozen=True)
class ScopedLine:
    invoice: PlannedInvoice
    line: PlannedLine
    from_supplier: bool


def scoped_lines(plan: list[PlannedInvoice], agreement: AgreementSpec,
                 term: TermSpec) -> list[ScopedLine]:
    last = min(agreement.ends_on, LAST_DAY)
    return [ScopedLine(invoice, line, invoice.supplier.key == agreement.supplier)
            for invoice in plan if agreement.starts_on <= invoice.on <= last
            for line in invoice.lines if line.product.key in term.products]
