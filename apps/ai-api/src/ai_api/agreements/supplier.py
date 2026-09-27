"""Linking an agreement's supplier to one the company already buys from."""
from __future__ import annotations

from sqlmodel import Session, col, select

from web_api.db.models import Invoice, Vendor
from web_api.vat import international_vat
from web_api.website import name_keys, site_root


def link_vendor(session: Session, company_id: str, *, vat_number: str | None,
                country_code: str | None, website: str | None,
                name: str | None) -> str | None:
    """The vendor with the same VAT number, else the only one with the same site or name."""
    vendors = session.exec(
        select(Vendor).where(col(Vendor.id).in_(
            select(Invoice.vendor_id).where(Invoice.company_id == company_id)
        ))
    ).all()
    wanted_vat = international_vat(vat_number, country_code)
    if wanted_vat:
        for vendor in vendors:
            if international_vat(vendor.vat_number, vendor.country_code) == wanted_vat:
                return vendor.id
    root = site_root(website)
    if root:
        by_site = [vendor for vendor in vendors if site_root(vendor.website) == root]
        if len(by_site) == 1:
            return by_site[0].id
    keys = name_keys(name or "")
    if keys:
        by_name = [vendor for vendor in vendors
                   if (vendor_keys := name_keys(vendor.name)) and vendor_keys[-1] == keys[-1]]
        if len(by_name) == 1:
            return by_name[0].id
    return None
