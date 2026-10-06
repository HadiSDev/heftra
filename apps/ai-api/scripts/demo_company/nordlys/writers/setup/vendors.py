"""The demo's suppliers in the shared supplier table, described as enrichment would have."""
from __future__ import annotations

from sqlmodel import Session

from web_api.db.models import Vendor

from ...catalog.shapes import SupplierSpec
from ...catalog.suppliers import SUPPLIERS
from ...ids import demo_id

COUNTRY = "DK"
DESCRIPTION_SOURCE = "web"


def write_vendors(session: Session) -> dict[str, Vendor]:
    """Create or update every supplier under its fixed id; returns them by supplier key."""
    vendors = {}
    for spec in SUPPLIERS:
        vendor_id = demo_id("vendor", spec.key)
        vendor = session.get(Vendor, vendor_id)
        if vendor is None:
            vendor = Vendor(id=vendor_id, name=spec.name)
        _describe(vendor, spec)
        session.add(vendor)
        vendors[spec.key] = vendor
    session.flush()
    return vendors


def _describe(vendor: Vendor, spec: SupplierSpec) -> None:
    vendor.name = spec.name
    vendor.country_code = COUNTRY
    vendor.vat_number = spec.vat_number
    vendor.website = spec.website
    vendor.description = spec.description
    vendor.description_source = DESCRIPTION_SOURCE
