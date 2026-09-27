"""Reading a FRED-style series CSV."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from web_api.price_indices.csv_file import SeriesFileError, parse_series_csv
from web_api.price_indices.values import IndexValue

FRED_CSV = """observation_date,CPIAUCSL
2025-09-01,324.245
2025-10-01,
2025-11-01,325.063
2025-12-01,.
"""


def test_months_with_values_are_read_in_order():
    assert parse_series_csv(FRED_CSV, "CPIAUCSL") == [
        IndexValue(date(2025, 9, 1), Decimal("324.245")),
        IndexValue(date(2025, 11, 1), Decimal("325.063")),
    ]


def test_the_older_date_header_is_accepted():
    text = "DATE,CPIAUCSL\n2023-01-01,300.42\n"

    assert parse_series_csv(text, "CPIAUCSL") == [IndexValue(date(2023, 1, 1), Decimal("300.42"))]


def test_a_date_is_read_as_its_month():
    text = "observation_date,CPIAUCSL\n2023-01-15,300.42\n"

    assert parse_series_csv(text, "CPIAUCSL")[0].month == date(2023, 1, 1)


def test_a_missing_series_column_is_named():
    with pytest.raises(SeriesFileError, match="no CPIAUCSL column"):
        parse_series_csv("observation_date,PCEPI\n2023-01-01,1\n", "CPIAUCSL")


def test_a_missing_date_column_is_named():
    with pytest.raises(SeriesFileError, match="no date column"):
        parse_series_csv("when,CPIAUCSL\n2023-01-01,1\n", "CPIAUCSL")


def test_an_unreadable_value_names_its_line():
    with pytest.raises(SeriesFileError, match="line 3"):
        parse_series_csv("DATE,CPIAUCSL\n2023-01-01,1\n2023-02-01,abc\n", "CPIAUCSL")
