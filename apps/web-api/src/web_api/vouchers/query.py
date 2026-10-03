"""The postings every voucher view reads: which are visible, and with what columns."""
from __future__ import annotations

from sqlalchemy import String, func, literal
from sqlmodel import Session, select

from web_api.db.models import ErpAccount, ErpEntry, Invoice, InvoiceLine, Vendor

from .rows import EntryRow

EXCLUDED_ENTRY_TYPES = ("payment",)

GROUP_KEY = func.coalesce(
    literal("v:", String) + ErpEntry.voucher_id,
    literal("e:", String) + ErpEntry.id,
)
"""The voucher a posting belongs to, or the posting itself when it has none; matches `bucket_key`."""


def sync_enabled_condition():
    """A posting is visible only if its account is still selected for sync."""
    return ErpEntry.erp_account_id.in_(
        select(ErpAccount.id).where(ErpAccount.sync_enabled == True)  # noqa: E712
    )


def visible_entry_conditions(company_ids: list[str]) -> list:
    """The postings of these companies that any voucher view shows: synced accounts, no payments."""
    return [
        ErpEntry.company_id.in_(company_ids),
        ErpEntry.entry_type.notin_(EXCLUDED_ENTRY_TYPES),
        sync_enabled_condition(),
    ]


def entry_select():
    """Base select yielding each entry with its account, vendor and category columns."""
    return (
        select(
            ErpEntry,
            ErpAccount.erp_account_code,
            ErpAccount.erp_account_name,
            Vendor.id,
            Vendor.name,
            ErpAccount.erp_account_type,
            InvoiceLine.level_1,
            InvoiceLine.level_2,
            InvoiceLine.level_3,
        )
        .join(ErpAccount, ErpAccount.id == ErpEntry.erp_account_id)
        .outerjoin(Invoice, Invoice.id == ErpEntry.source_invoice_id)
        .outerjoin(Vendor, Vendor.id == Invoice.vendor_id)
        .outerjoin(InvoiceLine, InvoiceLine.id == ErpEntry.source_invoice_line_id)
    )


def entry_rows(session: Session, statement) -> list[EntryRow]:
    """Run an `entry_select()` statement and name its columns."""
    return [EntryRow(*row) for row in session.exec(statement).all()]
