"""A voucher's emissions: its posted net spend split across its lines, in USD, times their factors."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from emission_factors import Factors, euro_rates
from spend_books import Books
from web_api.db.models import InvoiceLine
from web_api.emissions.status import EmissionsStatus
from web_api.emissions.vouchers import estimate_vouchers
from web_api.fx.provider import NullProvider
from web_api.fx.service import FxService
from web_api.vouchers.amounts import bucket_key
from web_api.vouchers.query import entry_rows, entry_select, visible_entry_conditions

ON = date(2026, 9, 3)


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def books(session) -> Books:
    books = Books(session)
    books.company.country_code = "DK"
    session.add(books.company)
    session.commit()
    euro_rates(session, ON, DKK="10", USD="1.45")
    return books


@pytest.fixture
def hosting(session) -> str:
    return Factors(session).sector("518200", "Hosting", {"DE": "0.5", "DK": "0.1"}).id


def _estimate(session, books):
    groups: dict = {}
    rows = entry_rows(session, entry_select().where(*visible_entry_conditions([books.company.id])))
    for row in rows:
        groups.setdefault(bucket_key(row.entry), []).append(row)
    return estimate_vouchers(session, groups, FxService(session, NullProvider()))


def _only(session, books):
    (result,) = _estimate(session, books).values()
    return result


def _match(session, invoice, *sectors: str | None) -> list[InvoiceLine]:
    lines = session.exec(select(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id)
                         .order_by(InvoiceLine.sequence)).all()
    for line, sector in zip(lines, sectors):
        line.emission_sector_id = sector
        session.add(line)
    session.commit()
    return list(lines)


def _supplier(books, name="Hetzner Online GmbH", country="DE"):
    vendor = books.supplier(name)
    vendor.country_code = country
    books.session.add(vendor)
    books.session.commit()
    return vendor


def test_a_single_line_voucher(session, books, hosting):
    invoice = books.purchase(ON, "1000.00", vendor=_supplier(books),
                             lines=[("1000.00", "Technology", "Hosting", "verified")])
    (line,) = _match(session, invoice, hosting)

    result = _only(session, books)

    assert result.status is EmissionsStatus.ESTIMATED
    assert result.kg_co2e == Decimal("72.500")
    assert result.estimated_spend == Decimal("1000.00")
    assert result.lines[line.id].area == "DE"


def test_the_posted_net_is_used_not_the_printed_gross(session, books, hosting):
    invoice = books.purchase(ON, "1000.00", vat="250.00", vendor=_supplier(books),
                             lines=[("1250.00", "Technology", "Hosting", "verified")])
    _match(session, invoice, hosting)

    assert _only(session, books).kg_co2e == Decimal("72.500")


def test_a_discount_without_a_sector_is_absorbed(session, books, hosting):
    invoice = books.purchase(ON, "46.40", vendor=_supplier(books), lines=[
        ("58.00", "Technology", "Hosting", "verified"),
        ("-11.60", None, None, "uncategorized"),
    ])
    _match(session, invoice, hosting, None)

    result = _only(session, books)

    assert result.status is EmissionsStatus.ESTIMATED
    assert result.estimated_spend == Decimal("46.40")


def test_half_matched_is_partial(session, books, hosting):
    invoice = books.purchase(ON, "1000.00", vendor=_supplier(books), lines=[
        ("500.00", "Technology", "Hosting", "verified"),
        ("500.00", "Technology", "Support", "verified"),
    ])
    _match(session, invoice, hosting, None)

    result = _only(session, books)

    assert result.status is EmissionsStatus.PARTIAL
    assert result.estimated_spend == Decimal("500.00")
    assert result.kg_co2e == Decimal("36.250")


def test_a_voucher_without_lines(session, books, hosting):
    books.purchase(ON, "25.00")

    assert _only(session, books).status is EmissionsStatus.NO_LINES


def test_no_line_has_a_sector(session, books, hosting):
    books.purchase(ON, "25.00", vendor=_supplier(books),
                   lines=[("25.00", "Technology", "Hosting", "verified")])

    result = _only(session, books)

    assert result.status is EmissionsStatus.UNMATCHED
    assert result.kg_co2e is None


def test_no_factor_for_any_country_tried(session, books):
    sector = Factors(session).sector("541100", "Legal services", {"US": "0.05"}).id
    invoice = books.purchase(ON, "25.00", vendor=_supplier(books),
                             lines=[("25.00", "Professional Services", "Legal", "verified")])
    _match(session, invoice, sector)

    assert _only(session, books).status is EmissionsStatus.NO_FACTOR


def test_no_rate_for_the_day_is_unconverted(session, books, hosting):
    invoice = books.purchase(date(2026, 9, 4), "25.00", vendor=_supplier(books),
                             lines=[("25.00", "Technology", "Hosting", "verified")])
    _match(session, invoice, hosting)

    assert _only(session, books).status is EmissionsStatus.UNCONVERTED


def test_no_active_factor_set(session, books):
    books.purchase(ON, "25.00")

    assert _only(session, books).status is EmissionsStatus.NO_FACTOR_SET


def test_a_supplier_without_a_country_uses_the_companys(session, books, hosting):
    invoice = books.purchase(ON, "1000.00", vendor=books.supplier("Unknown ApS"),
                             lines=[("1000.00", "Technology", "Hosting", "verified")])
    (line,) = _match(session, invoice, hosting)

    result = _only(session, books)

    assert result.lines[line.id].area == "DK"
    assert result.kg_co2e == Decimal("14.500")


def test_the_printed_country_stands_in_for_a_vendor_without_one(session, books, hosting):
    invoice = books.purchase(ON, "1000.00", vendor=books.supplier("Unknown GmbH"),
                             lines=[("1000.00", "Technology", "Hosting", "verified")])
    invoice.document_supplier_country_code = "DE"
    session.add(invoice)
    session.commit()
    (line,) = _match(session, invoice, hosting)

    assert _only(session, books).lines[line.id].area == "DE"
