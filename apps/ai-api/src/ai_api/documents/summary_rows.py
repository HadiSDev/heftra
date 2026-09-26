"""Rows that state a total rather than a thing bought."""
from __future__ import annotations

import re
from typing import Protocol, TypeVar

_SUMMARY_LABELS = {
    "samlet pris", "pris i alt", "i alt", "at betale", "total dkk", "subtotal",
    "moms", "beløb", "beløb i alt", "total i alt", "sum i alt",
    "total", "sub total", "sub-total", "grand total", "sum", "amount due",
    "balance due", "order total", "total amount", "net total", "total due",
    "vat", "tax", "total excl. vat", "total incl. vat", "items subtotal",
    "item(s) subtotal",
    "gesamt", "gesamtbetrag", "zwischensumme", "summe", "mwst", "nettobetrag",
    "rechnungsbetrag",
}


class _Row(Protocol):
    item_name: str | None
    description: str | None


RowT = TypeVar("RowT", bound=_Row)


def is_summary_row(label: str | None) -> bool:
    """Is this row a total rather than a thing bought?"""
    text = (label or "").strip().lower()
    if not text:
        return False
    text = re.sub(r"[\s:.\-–—]+$", "", text)
    text = re.sub(r"\s*\(?\d+([.,]\d+)?\s*%\)?$", "", text).strip()
    text = re.sub(r"\s+(dkk|eur|usd|gbp|sek|nok)$", "", text).strip()
    return text in _SUMMARY_LABELS


def without_summary_rows(rows: list[RowT]) -> list[RowT]:
    """The rows that are things bought; all of them when every row reads as a total."""
    itemised = [row for row in rows if not is_summary_row(row.item_name or row.description)]
    return itemised or rows
