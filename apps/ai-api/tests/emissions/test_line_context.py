"""A line's context: its text and category, its supplier, and its invoice's other lines."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session

from ai_api.emissions.line_context import line_contexts
from web_api.db.models import Company, Invoice, InvoiceLine, Organization, Vendor


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _invoice(session, *, vendor: Vendor | None = None, printed_country=None) -> Invoice:
    organization = Organization(name="Org", clerk_org_id="clerk_ctx")
    session.add(organization)
    session.commit()
    company = Company(organization_id=organization.id, name="Acme", base_currency="DKK")
    session.add(company)
    session.commit()
    invoice = Invoice(company_id=company.id, vendor_id=vendor.id if vendor else None,
                      currency="EUR", status="uncategorized",
                      document_supplier_country_code=printed_country)
    session.add(invoice)
    session.commit()
    return invoice


def _line(session, invoice, sequence, name, **fields) -> InvoiceLine:
    line = InvoiceLine(company_id=invoice.company_id, invoice_id=invoice.id, sequence=sequence,
                       item_name=name, status="uncategorized", **fields)
    session.add(line)
    session.commit()
    return line


def test_a_line_knows_its_supplier_category_and_neighbours(session):
    vendor = Vendor(name="Hetzner Online GmbH", country_code="DE",
                    description="German hosting company.", website="https://hetzner.com")
    session.add(vendor)
    session.commit()
    invoice = _invoice(session, vendor=vendor)
    line = _line(session, invoice, 0, "AX41", amount=Decimal("39.00"),
                 level_1="Indirect", level_2="Technology", level_3="Cloud & Hosting")
    _line(session, invoice, 1, "Backup space")

    (context,) = line_contexts(session, [line])

    assert context.category_path == ["Indirect", "Technology", "Cloud & Hosting"]
    assert (context.supplier_name, context.supplier_country) == ("Hetzner Online GmbH", "DE")
    assert context.supplier_description == "German hosting company."
    assert context.currency == "EUR"
    assert context.other_lines == ["Backup space"]


def test_the_printed_country_stands_in_for_a_supplier_without_one(session):
    invoice = _invoice(session, printed_country="SE")
    line = _line(session, invoice, 0, "Consulting")

    (context,) = line_contexts(session, [line])

    assert context.supplier_country == "SE"
    assert context.supplier_name is None


def test_the_same_question_has_the_same_key_whatever_its_spacing_or_case(session):
    invoice = _invoice(session)
    first = _line(session, invoice, 0, "Monthly  licence")
    second = _line(session, invoice, 1, "monthly licence")

    a, b = line_contexts(session, [first, second])

    assert a.question_key == b.question_key
