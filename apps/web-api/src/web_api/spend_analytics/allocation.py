"""Posted net expense per voucher, split across its lines' categories and given to its supplier.

A category is a line's second tree level and a subcategory its third: the first level only splits
direct from indirect spend, as the spend-by-category report already assumes.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import NamedTuple

from sqlmodel import Session, select

from web_api.db.models import Company, ErpEntry, InvoiceLine
from web_api.db.models.enums import LineStatus
from web_api.vouchers import shares
from web_api.vouchers.dates import spent_on as voucher_date
from web_api.vouchers.amounts import ZERO, bucket_key, group_invoice_id, shared_value, voucher_amount
from web_api.vouchers.query import entry_rows, entry_select, visible_entry_conditions
from web_api.vouchers.rows import EntryRow

from .periods import Period

CATEGORIZED = {LineStatus.AI_CATEGORIZED.value, LineStatus.VERIFIED.value}

CATEGORY_LEVEL = InvoiceLine.level_2
SUBCATEGORY_LEVEL = InvoiceLine.level_3

CategoryKey = tuple[str | None, str | None]
NOT_CATEGORIZED: CategoryKey = (None, None)


class AllocatedSpend(NamedTuple):
    """The part of one voucher's spend that went to one category."""

    company_id: str
    currency: str
    voucher: str
    invoice_id: str | None
    vendor_id: str | None
    spent_on: date
    category: str | None
    subcategory: str | None
    categorized: bool
    amount: Decimal


class UnconvertedVoucher(NamedTuple):
    """A voucher whose postings could not be converted to its company's base currency."""

    company_id: str
    currency: str
    spent_on: date


class Allocation(NamedTuple):
    spend: list[AllocatedSpend]
    unconverted: list[UnconvertedVoucher]


class _LineWeight(NamedTuple):
    invoice_id: str
    key: CategoryKey
    amount: Decimal


def allocate(session: Session, company_ids: list[str], window: Period) -> Allocation:
    """Every voucher's spend in the window, attributed to its supplier and its lines' categories."""
    if not company_ids:
        return Allocation([], [])

    rows = entry_rows(
        session,
        entry_select().where(
            *visible_entry_conditions(company_ids),
            ErpEntry.accounting_date >= window.start,
            ErpEntry.accounting_date <= window.end,
        ),
    )
    vouchers: dict[tuple[str, str], list[EntryRow]] = {}
    for row in rows:
        vouchers.setdefault(bucket_key(row.entry), []).append(row)

    currencies = _base_currencies(session, company_ids)
    invoice_ids = {
        invoice_id for group in vouchers.values() if (invoice_id := group_invoice_id(group))
    }
    weights = _line_weights(session, invoice_ids)

    spend: list[AllocatedSpend] = []
    unconverted: list[UnconvertedVoucher] = []
    for (company_id, voucher), group in vouchers.items():
        spent_on = voucher_date(group)
        currency = currencies[company_id]
        amount, _, _, _, unconverted_count = voucher_amount(group, "base")
        if unconverted_count:
            unconverted.append(UnconvertedVoucher(company_id, currency, spent_on))
        if not amount:
            continue
        invoice_id = group_invoice_id(group)
        vendor_id = shared_value([row.vendor_id for row in group if row.vendor_id])
        for (category, subcategory), part in split(amount, weights.get(invoice_id, {})).items():
            spend.append(AllocatedSpend(
                company_id=company_id, currency=currency, voucher=voucher,
                invoice_id=invoice_id, vendor_id=vendor_id, spent_on=spent_on,
                category=category, subcategory=subcategory,
                categorized=(category, subcategory) != NOT_CATEGORIZED, amount=part,
            ))
    return Allocation(spend, unconverted)


def split(amount: Decimal, weights: dict[CategoryKey, Decimal]) -> dict[CategoryKey, Decimal]:
    """`amount` shared out across categories by `weights`; with none, all of it is uncategorized."""
    return shares.split(amount, weights) or {NOT_CATEGORIZED: amount}


def _line_weights(session: Session, invoice_ids: set[str]) -> dict[str, dict[CategoryKey, Decimal]]:
    """`{invoice_id: {category: the lines' value in it}}`, uncategorized lines under one key.

    An uncategorized line below zero, such as a discount, is left out: the posting already nets it,
    so the voucher's other parts absorb it in proportion rather than "Not categorized" going negative.
    """
    if not invoice_ids:
        return {}
    lines = session.exec(
        select(InvoiceLine.invoice_id, InvoiceLine.status, CATEGORY_LEVEL,
               SUBCATEGORY_LEVEL, InvoiceLine.base_amount)
        .where(InvoiceLine.invoice_id.in_(invoice_ids), InvoiceLine.base_amount.is_not(None))
    ).all()
    weights: dict[str, dict[CategoryKey, Decimal]] = {}
    for line in (_weight(*line) for line in lines):
        if line.key == NOT_CATEGORIZED and line.amount < 0:
            continue
        per_invoice = weights.setdefault(line.invoice_id, {})
        per_invoice[line.key] = per_invoice.get(line.key, ZERO) + line.amount
    return weights


def _weight(invoice_id: str, status: str, category: str | None, subcategory: str | None,
            amount: Decimal) -> _LineWeight:
    if str(status) in CATEGORIZED and category:
        return _LineWeight(invoice_id, (category, subcategory), amount)
    return _LineWeight(invoice_id, NOT_CATEGORIZED, amount)


def _base_currencies(session: Session, company_ids: list[str]) -> dict[str, str]:
    return dict(session.exec(
        select(Company.id, Company.base_currency).where(Company.id.in_(company_ids))
    ).all())
