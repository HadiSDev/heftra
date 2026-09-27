"""Filling an agreement's header from what was read, without undoing a person's edits."""
from __future__ import annotations

from datetime import date
from pathlib import PurePath

from web_api.db.models import Agreement, File
from web_api.vat import international_vat
from web_api.website import site_root

from .models import ReadHeader


def apply_header(agreement: Agreement, file_row: File | None, header: ReadHeader) -> None:
    """Set what the agreement doesn't have yet; the title only while it is still the file name."""
    country = (header.supplier_country_code or "").strip().upper() or None
    default_title = PurePath(file_row.filename).stem if file_row else agreement.title
    if header.title and agreement.title == default_title:
        agreement.title = header.title.strip()
    agreement.reference = agreement.reference or _text(header.reference)
    agreement.supplier_name = agreement.supplier_name or _text(header.supplier_name)
    agreement.supplier_vat_number = agreement.supplier_vat_number or international_vat(
        header.supplier_vat_number, country)
    agreement.supplier_website = agreement.supplier_website or site_root(header.supplier_website)
    agreement.starts_on = agreement.starts_on or _day(header.starts_on)
    agreement.ends_on = agreement.ends_on or _day(header.ends_on)
    agreement.currency = agreement.currency or _currency(header.currency)
    agreement.summary = agreement.summary or _text(header.summary)


def supplier_country(header: ReadHeader) -> str | None:
    return (header.supplier_country_code or "").strip().upper() or None


def _text(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _day(value: str | None) -> date | None:
    try:
        return date.fromisoformat((value or "").strip()[:10])
    except ValueError:
        return None


def _currency(value: str | None) -> str | None:
    code = (value or "").strip().upper()
    return code if len(code) == 3 and code.isalpha() else None
