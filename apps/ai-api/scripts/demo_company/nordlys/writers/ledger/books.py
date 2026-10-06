"""What the ledger is written against: suppliers, categories, accounts and emission sectors."""
from __future__ import annotations

from dataclasses import dataclass

from web_api.db.models import EmissionSector, ErpAccount, SpendCategory, Vendor

from ...generation.planned import PlannedInvoice, PlannedLine
from ...ids import demo_id


@dataclass(frozen=True)
class Books:
    """`leaves` by category code, `accounts` by account code, `sectors` by sector code and
    `vendors` by supplier key."""

    vendors: dict[str, Vendor]
    leaves: dict[str, SpendCategory]
    accounts: dict[str, ErpAccount]
    sectors: dict[str, EmissionSector]


def invoice_id(invoice: PlannedInvoice) -> str:
    return demo_id("invoice", invoice.key)


def line_id(invoice: PlannedInvoice, line: PlannedLine) -> str:
    return demo_id("invoice-line", f"{invoice.key}:{line.sequence}")
