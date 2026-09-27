"""The dashboard's emissions: the period, its comparison, twelve months and the top sectors."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from emission_factors import Factors, euro_rates
from spend_books import Books
from web_api.db.models import InvoiceLine
from web_api.spend_analytics.emissions import spend_emissions
from web_api.spend_analytics.periods import Period

SEPTEMBER = Period(date(2026, 9, 1), date(2026, 9, 30))


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _matched(session, invoice, sector_id):
    for line in session.exec(select(InvoiceLine).where(InvoiceLine.invoice_id == invoice.id)):
        line.emission_sector_id = sector_id
        session.add(line)
    session.commit()


def test_the_period_its_comparison_and_the_months(session):
    books = Books(session)
    books.company.country_code = "DK"
    session.add(books.company)
    session.commit()
    factors = Factors(session)
    hosting = factors.sector("518200", "Hosting", {"DK": "0.5"}).id
    travel = factors.sector("481000", "Air transportation", {"DK": "1.0"}).id
    for day in (date(2026, 9, 3), date(2026, 8, 3)):
        euro_rates(session, day, DKK="10", USD="1.00")
    supplier = books.supplier("Supplier ApS")
    _matched(session, books.purchase(date(2026, 9, 3), "300.00", vendor=supplier,
                                     lines=[("300", "Technology", "Hosting", "verified")]), hosting)
    _matched(session, books.purchase(date(2026, 9, 3), "200.00", vendor=supplier,
                                     lines=[("200", "Travel", "Air", "verified")]), travel)
    _matched(session, books.purchase(date(2026, 8, 3), "400.00", vendor=supplier,
                                     lines=[("400", "Technology", "Hosting", "verified")]), hosting)
    books.purchase(date(2026, 9, 4), "100.00")

    report = spend_emissions(session, [books.company.id], SEPTEMBER)

    assert report.kg_co2e == Decimal("35.000")
    assert report.comparison_kg_co2e == Decimal("20.000")
    months = {month.month: month.kg_co2e for month in report.months}
    assert (months[date(2026, 9, 1)], months[date(2026, 8, 1)]) == (Decimal("35.000"),
                                                                    Decimal("20.000"))
    assert [(row.currency, row.posted_spend, row.estimated_spend) for row in report.spend] == [
        ("DKK", Decimal("600.00"), Decimal("500.00"))]
    assert [(sector.code, sector.kg_co2e) for sector in report.top_sectors] == [
        ("481000", Decimal("20.000")), ("518200", Decimal("15.000"))]
    assert report.factor_set.attribution == "CEDA by Watershed"


def test_without_a_factor_set_there_are_no_figures(session):
    books = Books(session)
    books.purchase(date(2026, 9, 3), "300.00")

    report = spend_emissions(session, [books.company.id], SEPTEMBER)

    assert report.factor_set is None
    assert report.kg_co2e is None
    assert report.months == []
