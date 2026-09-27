"""Whether a line was bought from the agreement's supplier."""
from __future__ import annotations

from web_api.db.models import Agreement

from .lines import AnalysedLine


def supplier_vat(agreement: Agreement, vendor_vat: str | None) -> str | None:
    """The VAT number to recognise the supplier by: the agreement's, else its linked vendor's."""
    return agreement.supplier_vat_number or vendor_vat


def from_supplier(line: AnalysedLine, vendor_id: str | None, vat: str | None) -> bool:
    if vendor_id is not None and line.vendor_id == vendor_id:
        return True
    return vat is not None and line.vendor_vat == vat
