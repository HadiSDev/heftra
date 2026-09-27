"""The vouchers a date window holds, each as its listed postings."""
from __future__ import annotations

from datetime import date

from sqlmodel import Session

from ..db.models import ErpEntry
from .amounts import bucket_key
from .query import entry_rows, entry_select, visible_entry_conditions
from .rows import EntryRow

VoucherKey = tuple[str, str]


def vouchers_between(session: Session, company_ids: list[str], start: date,
                     end: date) -> dict[VoucherKey, list[EntryRow]]:
    """`{(company_id, voucher): postings}` for postings dated from `start` to `end`, inclusive."""
    if not company_ids:
        return {}
    rows = entry_rows(
        session,
        entry_select().where(
            *visible_entry_conditions(company_ids),
            ErpEntry.accounting_date >= start,
            ErpEntry.accounting_date <= end,
        ),
    )
    vouchers: dict[VoucherKey, list[EntryRow]] = {}
    for row in rows:
        vouchers.setdefault(bucket_key(row.entry), []).append(row)
    return vouchers
