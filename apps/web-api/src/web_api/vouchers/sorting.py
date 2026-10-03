"""How the voucher list is ordered: one aggregate per sortable column, over each voucher's postings."""
from __future__ import annotations

from typing import Literal

from sqlalchemy import and_, case, func, nulls_last
from sqlmodel import select

from web_api.db.models import ErpAccount, ErpEntry, Invoice, Vendor
from web_api.db.models.enums import EXPENSE_ACCOUNT_TYPE

from .amounts import ZERO
from .query import GROUP_KEY

VoucherSort = Literal["accounting_date", "voucher_number", "vendor_name", "amount"]
SortOrder = Literal["asc", "desc"]

DEFAULT_SORT: VoucherSort = "accounting_date"

LAST_DATE = func.max(ErpEntry.accounting_date)

_VOUCHER_NUMBER = case(
    (func.min(ErpEntry.voucher_number) == func.max(ErpEntry.voucher_number),
     func.max(ErpEntry.voucher_number)),
)

_VENDOR_NAME = case(
    (and_(func.min(Vendor.name) == func.max(Vendor.name), func.count(Vendor.name) == func.count()),
     func.max(Vendor.name)),
)

_CONVERTED = ErpEntry.base_currency.is_not(None)

_EXPENSE_NET = func.sum(case(
    (and_(_CONVERTED, ErpAccount.erp_account_type == EXPENSE_ACCOUNT_TYPE),
     func.coalesce(ErpEntry.base_debit_amount, ZERO) - func.coalesce(ErpEntry.base_credit_amount, ZERO)),
))

_UNTYPED_DEBIT = case(
    (func.count(case((and_(_CONVERTED, ErpAccount.erp_account_type.is_not(None)), 1))) == 0,
     func.sum(case((_CONVERTED, func.coalesce(ErpEntry.base_debit_amount, ZERO))))),
)

_BASE_AMOUNT = func.coalesce(_EXPENSE_NET, _UNTYPED_DEBIT)

_SORT_KEYS = {
    "accounting_date": (LAST_DATE,),
    "voucher_number": (func.length(_VOUCHER_NUMBER), _VOUCHER_NUMBER),
    "vendor_name": (_VENDOR_NAME,),
    "amount": (_BASE_AMOUNT,),
}
"""What each column orders by, matching what the list shows: the number or supplier every posting
agrees on, and the base-currency net spend `voucher_amount` computes. Voucher numbers order by
length first, so numeric ones run 9, 10, 11 rather than 10, 11, 9."""


def default_order(sort: VoucherSort) -> SortOrder:
    """The order a column sorts in when first chosen: supplier A–Z, figures and dates largest first."""
    return "asc" if sort == "vendor_name" else "desc"


def group_keys_select(conditions: list):
    """One row per voucher the conditions select: its company, group key and latest date."""
    return (
        select(ErpEntry.company_id, GROUP_KEY.label("group_key"), LAST_DATE.label("last_date"))
        .join(ErpAccount, ErpAccount.id == ErpEntry.erp_account_id)
        .outerjoin(Invoice, Invoice.id == ErpEntry.source_invoice_id)
        .outerjoin(Vendor, Vendor.id == Invoice.vendor_id)
        .where(*conditions)
        .group_by(ErpEntry.company_id, GROUP_KEY)
    )


def group_order(sort: VoucherSort, order: SortOrder) -> list:
    """ORDER BY for `group_keys_select`: the column, nulls last, then newest first and the group key."""
    chosen = [
        nulls_last(key.asc() if order == "asc" else key.desc())
        for key in _SORT_KEYS[sort]
    ]
    newest_first = [] if sort == "accounting_date" else [nulls_last(LAST_DATE.desc())]
    return [*chosen, *newest_first, GROUP_KEY, ErpEntry.company_id]
