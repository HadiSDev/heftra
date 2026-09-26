"""What a voucher's postings add up to: its net spend, its totals and the invoice they share."""
from __future__ import annotations

from decimal import Decimal

from web_api.db.models import ErpEntry
from web_api.db.models.enums import EXPENSE_ACCOUNT_TYPE

from .rows import EntryRow

ZERO = Decimal("0")

AMOUNT_FIELDS = {
    "original": ("debit_amount", "credit_amount", "currency"),
    "base": ("base_debit_amount", "base_credit_amount", "base_currency"),
}


def bucket_key(entry: ErpEntry) -> tuple[str, str]:
    """The (company, group key) a posting belongs to: its voucher, or itself when it has none."""
    if entry.voucher_id is not None:
        return entry.company_id, f"v:{entry.voucher_id}"
    return entry.company_id, f"e:{entry.id}"


def shared_value(values: list) -> object | None:
    """The one value every entry agrees on, or None if they disagree."""
    distinct = {v for v in values}
    if len(distinct) == 1:
        return next(iter(distinct))
    return None


def group_invoice_id(rows: list[EntryRow]) -> str | None:
    """The source invoice the group's postings agree on, if any."""
    return shared_value([r.entry.source_invoice_id for r in rows if r.entry.source_invoice_id])


def net_spend(rows: list[EntryRow], debit_field: str, credit_field: str) -> Decimal | None:
    """The group's signed net spend on expense accounts, or None when it spent nothing."""
    expense_rows = [r for r in rows if r.account_type == EXPENSE_ACCOUNT_TYPE]
    if not expense_rows:
        return None
    return sum(
        (
            (getattr(r.entry, debit_field) or ZERO) - (getattr(r.entry, credit_field) or ZERO)
            for r in expense_rows
        ),
        ZERO,
    )


def voucher_amount(
    rows: list[EntryRow], mode: str
) -> tuple[Decimal | None, Decimal | None, Decimal | None, str | None, int]:
    """Net spend, debit/credit totals, currency and unconverted count for one voucher."""
    debit_field, credit_field, currency_field = AMOUNT_FIELDS[mode]

    if mode == "base":
        summable = [r for r in rows if r.entry.base_currency is not None]
        unconverted_count = len(rows) - len(summable)
    else:
        summable = rows
        unconverted_count = 0

    if not summable:
        return None, None, None, None, unconverted_count

    debit_total = sum((getattr(r.entry, debit_field) or ZERO for r in summable), ZERO)
    credit_total = sum((getattr(r.entry, credit_field) or ZERO for r in summable), ZERO)
    amount = net_spend(summable, debit_field, credit_field)
    if amount is None and not any(r.account_type for r in summable):
        amount = debit_total
    currency = shared_value([getattr(r.entry, currency_field) for r in summable])
    return amount, debit_total, credit_total, currency, unconverted_count
