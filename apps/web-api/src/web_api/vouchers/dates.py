"""The date a voucher's spend falls on."""
from __future__ import annotations

from datetime import date

from ..db.models.enums import EXPENSE_ACCOUNT_TYPE
from .rows import EntryRow


def spent_on(group: list[EntryRow]) -> date:
    """The earliest accounting date among the voucher's expense postings, else among all of them."""
    expense = [row.entry.accounting_date for row in group if row.account_type == EXPENSE_ACCOUNT_TYPE]
    return min(expense or [row.entry.accounting_date for row in group])
