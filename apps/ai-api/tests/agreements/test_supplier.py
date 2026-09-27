"""Linking an agreement's supplier to one the company already buys from."""
from __future__ import annotations

from datetime import date

from sqlmodel import Session

from ai_api.agreements.supplier import link_vendor
from web_api.db.models import Invoice, Vendor


def _bought_from(engine, company_id: str, **vendor_fields) -> str:
    with Session(engine) as s:
        vendor = Vendor(**vendor_fields)
        s.add(vendor)
        s.commit()
        s.add(Invoice(company_id=company_id, vendor_id=vendor.id, invoice_number=vendor.name,
                      invoice_date=date(2026, 1, 1), currency="DKK", status="posted"))
        s.commit()
        return vendor.id


def _link(engine, company_id: str, **header) -> str | None:
    fields = {"vat_number": None, "country_code": None, "website": None, "name": None, **header}
    with Session(engine) as s:
        return link_vendor(s, company_id, **fields)


def test_the_same_vat_number_links(engine, make_tenant):
    company_id = make_tenant()["company_id"]
    atea = _bought_from(engine, company_id, name="Atea A/S", vat_number="DK12345678",
                        country_code="DK")

    assert _link(engine, company_id, vat_number="12345678", country_code="DK") == atea


def test_the_same_website_links(engine, make_tenant):
    company_id = make_tenant()["company_id"]
    atea = _bought_from(engine, company_id, name="Atea", website="https://www.atea.dk/")

    assert _link(engine, company_id, website="www.atea.dk") == atea


def test_the_same_name_links_only_when_it_is_the_only_one(engine, make_tenant):
    company_id = make_tenant()["company_id"]
    _bought_from(engine, company_id, name="Atea A/S")
    _bought_from(engine, company_id, name="ATEA ApS")

    assert _link(engine, company_id, name="Atea") is None


def test_suppliers_of_other_companies_are_not_linked(engine, make_tenant):
    mine = make_tenant("Acme")["company_id"]
    theirs = make_tenant("Beta")["company_id"]
    _bought_from(engine, theirs, name="Atea A/S", vat_number="DK12345678")

    assert _link(engine, mine, vat_number="DK12345678") is None
