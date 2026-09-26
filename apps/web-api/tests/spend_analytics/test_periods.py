"""A reporting period, the one it is compared with, and the months that end with it."""
from __future__ import annotations

from datetime import date

import pytest

from web_api.spend_analytics.periods import Period, trailing_months


def test_a_quarter_is_compared_with_the_quarter_before():
    period = Period(date(2026, 7, 1), date(2026, 9, 30))

    assert period.comparison() == Period(date(2026, 4, 1), date(2026, 6, 30))


def test_a_quarter_to_date_is_compared_with_the_same_days_of_the_quarter_before():
    period = Period(date(2026, 7, 1), date(2026, 9, 26))

    assert period.comparison() == Period(date(2026, 4, 1), date(2026, 6, 26))


def test_a_month_to_date_is_compared_with_the_same_days_of_the_month_before():
    assert Period(date(2026, 9, 1), date(2026, 9, 26)).comparison() == Period(
        date(2026, 8, 1), date(2026, 8, 26)
    )


def test_a_year_to_date_is_compared_with_the_months_before_it():
    assert Period(date(2026, 1, 1), date(2026, 9, 26)).comparison() == Period(
        date(2025, 4, 1), date(2025, 12, 26)
    )


def test_a_whole_month_ending_short_is_compared_with_the_whole_month_before():
    assert Period(date(2026, 3, 1), date(2026, 3, 31)).comparison() == Period(
        date(2026, 2, 1), date(2026, 2, 28)
    )


def test_any_other_period_is_compared_with_as_many_days_before_it():
    period = Period(date(2026, 7, 10), date(2026, 7, 19))

    assert period.days == 10
    assert period.comparison() == Period(date(2026, 6, 30), date(2026, 7, 9))


def test_a_period_holds_its_first_and_last_days():
    period = Period(date(2026, 7, 1), date(2026, 7, 31))

    assert period.contains(date(2026, 7, 1))
    assert period.contains(date(2026, 7, 31))
    assert not period.contains(date(2026, 8, 1))


def test_an_inverted_period_is_refused():
    with pytest.raises(ValueError):
        Period(date(2026, 9, 1), date(2026, 8, 1))


def test_the_twelve_months_ending_with_a_date_start_eleven_months_before_it():
    months = trailing_months(date(2026, 9, 26))

    assert months[0] == date(2025, 10, 1)
    assert months[-1] == date(2026, 9, 1)
    assert len(months) == 12


def test_the_window_of_months_covers_their_whole_span():
    months = trailing_months(date(2026, 2, 10), count=3)

    assert months == [date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)]
