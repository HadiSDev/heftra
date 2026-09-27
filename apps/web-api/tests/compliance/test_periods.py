"""The commitment period a date falls in."""
from __future__ import annotations

from datetime import date

from web_api.compliance.periods import CommitmentPeriod, commitment_period

START = date(2025, 2, 15)


def test_a_yearly_commitment_counts_from_the_start_date():
    assert commitment_period("year", START, None, date(2026, 6, 1)) == CommitmentPeriod(
        date(2026, 2, 15), date(2027, 2, 14))


def test_a_quarter_holds_today():
    assert commitment_period("quarter", START, None, date(2025, 6, 1)) == CommitmentPeriod(
        date(2025, 5, 15), date(2025, 8, 14))


def test_a_period_stops_at_the_agreement_s_end():
    assert commitment_period("year", START, date(2025, 12, 31), date(2025, 6, 1)) == \
        CommitmentPeriod(START, date(2025, 12, 31))


def test_after_the_end_the_last_period_is_kept():
    assert commitment_period("year", START, date(2026, 6, 30), date(2027, 3, 1)) == \
        CommitmentPeriod(date(2026, 2, 15), date(2026, 6, 30))


def test_the_whole_agreement_is_one_period():
    assert commitment_period("agreement", START, date(2026, 2, 14), date(2025, 6, 1)) == \
        CommitmentPeriod(START, date(2026, 2, 14))


def test_month_ends_are_kept_within_short_months():
    assert commitment_period("month", date(2025, 1, 31), None, date(2025, 2, 20)) == \
        CommitmentPeriod(date(2025, 1, 31), date(2025, 2, 27))
