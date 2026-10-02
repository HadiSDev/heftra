"""Whether a line was bought from the agreement's supplier."""
from __future__ import annotations

from sqlmodel import Session, select

from web_api.db.models import Agreement, Invoice, Vendor
from web_api.vat import international_vat

from .lines import AnalysedLine


def supplier_vat(agreement: Agreement, vendor_vat: str | None) -> str | None:
    """The VAT number to recognise the supplier by: the agreement's, else its linked vendor's."""
    return agreement.supplier_vat_number or vendor_vat


def from_supplier(line: AnalysedLine, vendor_id: str | None, vat: str | None) -> bool:
    if vendor_id is not None and line.vendor_id == vendor_id:
        return True
    return vat is not None and line.vendor_vat == vat


def supplier_vendor_ids(session: Session, agreement: Agreement, vat: str | None) -> set[str]:
    """The vendors of the company's invoices that count as the agreement's supplier."""
    ids = {agreement.vendor_id} if agreement.vendor_id else set()
    if vat is None:
        return ids
    for vendor_id, vat_number, country in session.exec(
        select(Vendor.id, Vendor.vat_number, Vendor.country_code).distinct()
        .join(Invoice, Invoice.vendor_id == Vendor.id)
        .where(Invoice.company_id == agreement.company_id)
    ).all():
        if international_vat(vat_number, country) == vat:
            ids.add(vendor_id)
    return ids
