"""Taking money converted at the voucher date back to the factor set's price year."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from emission_factors import Factors, consumer_prices
from web_api.emissions.deflation import Deflator


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def test_a_dollar_set_is_deflated_with_us_cpi(session):
    factor_set = Factors(session).factor_set
    consumer_prices(session, m2026_08="330")

    deflation = Deflator.for_factor_set(session, factor_set).for_date(date(2026, 8, 14))

    assert (deflation.series, deflation.label) == ("CPIAUCSL", "US CPI")
    assert (deflation.month, deflation.index) == (date(2026, 8, 1), Decimal("330"))
    assert (deflation.base_year, deflation.base_index) == (2023, Decimal("300"))
    assert deflation.ratio == Decimal("300") / Decimal("330")


def test_a_gap_is_filled_by_the_month_before(session):
    factor_set = Factors(session).factor_set
    consumer_prices(session, m2025_09="324.245", m2025_11="325.063")

    deflation = Deflator.for_factor_set(session, factor_set).for_date(date(2025, 10, 12))

    assert (deflation.month, deflation.index) == (date(2025, 9, 1), Decimal("324.245"))


def test_without_values_there_is_no_deflator(session):
    assert Deflator.for_factor_set(session, Factors(session).factor_set) is None


def test_an_incomplete_price_year_has_no_deflator(session):
    factor_set = Factors(session).factor_set
    consumer_prices(session, year=2024)

    assert Deflator.for_factor_set(session, factor_set) is None


def test_a_currency_without_an_index_has_no_deflator(session):
    factor_set = Factors(session).factor_set
    factor_set.currency = "EUR"
    consumer_prices(session)

    assert Deflator.for_factor_set(session, factor_set) is None
