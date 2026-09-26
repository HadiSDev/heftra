"""Tally how much of the posted spend has been categorized, per base currency.

A voucher's categorized spend is its posted spend in the share its categorized lines hold of its lines'
value. The lines give the split and the ledger the amount, so lines printed with VAT, a discount the
lines leave out, or conversion rounding cannot take the categorized spend past the posted spend.
"""
from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple

from . import config
from .db.models.enums import LineStatus
from .schemas import SpendCoverageRow

_CATEGORIZED = {LineStatus.AI_CATEGORIZED.value, LineStatus.VERIFIED.value}
_ZERO = Decimal("0")
_CENT = Decimal("0.01")


class VoucherSpend(NamedTuple):
    """One listed voucher's net spend in its company's base currency."""

    company_id: str
    amount: Decimal | None
    unconverted: bool
    invoice_id: str | None = None


class LineState(NamedTuple):
    """The categorization facts about one line that the summary counts."""

    company_id: str
    status: str
    confidence: Decimal | None
    base_amount: Decimal | None
    invoice_id: str | None = None


def needs_review(line: LineState) -> bool:
    """An AI categorization too uncertain to trust unseen."""
    if line.status != LineStatus.AI_CATEGORIZED.value:
        return False
    if line.confidence is None:
        return True
    return line.confidence < Decimal(str(config.CATEGORIZATION_REVIEW_THRESHOLD))


def categorized_share(lines: list[LineState]) -> Decimal:
    """The share, between 0 and 1, of the lines' value that is categorized."""
    total = sum((line.base_amount or _ZERO for line in lines), _ZERO)
    if total <= 0:
        return _ZERO
    categorized = sum(
        (line.base_amount or _ZERO for line in lines if line.status in _CATEGORIZED), _ZERO
    )
    return min(max(categorized / total, _ZERO), Decimal("1"))


def _count_line(row: SpendCoverageRow, line: LineState) -> None:
    row.line_count += 1
    if line.status in _CATEGORIZED:
        row.categorized_lines += 1
    if line.status == LineStatus.VERIFIED.value:
        row.verified_lines += 1
    if line.status == LineStatus.UNCATEGORIZED.value:
        row.uncategorized_lines += 1
    if line.status == LineStatus.AI_FAILED.value:
        row.failed_lines += 1
    if needs_review(line):
        row.needs_review_lines += 1


def tally(
    vouchers: list[VoucherSpend],
    lines: list[LineState],
    base_currencies: dict[str, str],
) -> list[SpendCoverageRow]:
    """One row per base currency, summing vouchers and lines by their company's currency."""
    rows: dict[str, SpendCoverageRow] = {}

    def row_for(company_id: str) -> SpendCoverageRow:
        currency = base_currencies[company_id]
        if currency not in rows:
            rows[currency] = SpendCoverageRow(currency=currency)
        return rows[currency]

    lines_by_invoice: dict[str, list[LineState]] = {}
    for line in lines:
        if line.invoice_id is not None:
            lines_by_invoice.setdefault(line.invoice_id, []).append(line)

    for voucher in vouchers:
        row = row_for(voucher.company_id)
        row.voucher_count += 1
        if voucher.unconverted:
            row.unconverted_vouchers += 1
        if voucher.amount is not None:
            row.posted_spend += voucher.amount
            if voucher.invoice_id is not None:
                share = categorized_share(lines_by_invoice.get(voucher.invoice_id, []))
                row.categorized_spend += (voucher.amount * share).quantize(_CENT)
    for line in lines:
        _count_line(row_for(line.company_id), line)
    return sorted(rows.values(), key=lambda row: row.currency)
