"""A demo request is treated as automated when a bot gives itself away."""
from __future__ import annotations

from web_api.demo_requests.guard import is_automated_submission


def test_a_person_taking_their_time_is_not_automated():
    assert is_automated_submission(None, 0, 3_000) is False
    assert is_automated_submission("", 0, 60_000) is False


def test_a_filled_honeypot_is_automated():
    assert is_automated_submission("https://spam.example", 0, 60_000) is True


def test_a_submission_inside_three_seconds_is_automated():
    assert is_automated_submission(None, 0, 2_999) is True
