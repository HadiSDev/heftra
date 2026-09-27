"""A series' yearly average and the value for a date."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from web_api.db.models import PriceIndexValue
from web_api.price_indices.index import PriceIndex
from web_api.price_indices.series import US_CPI, index_for_currency
from web_api.price_indices.values import IndexValue


def _year(year: int, first: int) -> list[IndexValue]:
    return [IndexValue(date(year, month, 1), Decimal(first + month - 1)) for month in range(1, 13)]


def test_a_year_averages_its_twelve_months():
    index = PriceIndex(_year(2023, 300))

    assert index.average(2023) == Decimal("305.5")


def test_an_incomplete_year_has_no_average():
    index = PriceIndex(_year(2023, 300)[:11])

    assert index.average(2023) is None


def test_a_date_takes_its_months_value():
    index = PriceIndex(_year(2023, 300))

    assert index.at(date(2023, 3, 17)) == IndexValue(date(2023, 3, 1), Decimal(302))


def test_a_gap_takes_the_latest_earlier_month():
    index = PriceIndex([
        IndexValue(date(2025, 9, 1), Decimal("324.245")),
        IndexValue(date(2025, 11, 1), Decimal("325.063")),
    ])

    assert index.at(date(2025, 10, 12)) == IndexValue(date(2025, 9, 1), Decimal("324.245"))


def test_an_unpublished_month_takes_the_latest():
    index = PriceIndex([IndexValue(date(2026, 8, 1), Decimal("334.131"))])

    assert index.at(date(2026, 9, 20)).month == date(2026, 8, 1)
    assert index.latest_month == date(2026, 8, 1)


def test_a_date_before_the_series_has_no_value():
    index = PriceIndex(_year(2023, 300))

    assert index.at(date(2022, 12, 31)) is None


def test_an_empty_series():
    index = PriceIndex([])

    assert index.latest_month is None
    assert index.at(date(2026, 1, 1)) is None


def test_a_series_is_loaded_from_the_database(engine):
    with Session(engine) as session:
        session.add(PriceIndexValue(series="CPIAUCSL", month=date(2023, 1, 1),
                                    value=Decimal("300.42"), source="fred"))
        session.add(PriceIndexValue(series="PCEPI", month=date(2023, 1, 1),
                                    value=Decimal("120"), source="fred"))
        session.commit()

        index = PriceIndex.load(session, "CPIAUCSL")

    assert index.at(date(2023, 1, 9)) == IndexValue(date(2023, 1, 1), Decimal("300.42"))


def test_dollars_are_deflated_with_us_cpi():
    assert index_for_currency("usd") == US_CPI
    assert index_for_currency("EUR") is None
