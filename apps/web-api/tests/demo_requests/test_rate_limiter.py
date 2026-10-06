"""The sliding window forgets requests once they are an hour old."""
from __future__ import annotations

from web_api.demo_requests.rate_limiter import SlidingWindowRateLimiter

_HOUR = 3_600


def test_admits_up_to_the_limit_then_refuses():
    limiter = SlidingWindowRateLimiter(window_seconds=_HOUR)

    decisions = [limiter.admit("1.2.3.4", 2, now) for now in (0, 10, 20)]

    assert [decision.allowed for decision in decisions] == [True, True, False]


def test_retry_after_counts_down_to_the_oldest_request_leaving_the_window():
    limiter = SlidingWindowRateLimiter(window_seconds=_HOUR)
    limiter.admit("1.2.3.4", 1, 100)

    decision = limiter.admit("1.2.3.4", 1, 400)

    assert decision.allowed is False
    assert decision.retry_after_seconds == _HOUR - 300


def test_window_slides_rather_than_resetting():
    limiter = SlidingWindowRateLimiter(window_seconds=_HOUR)
    limiter.admit("1.2.3.4", 2, 0)
    limiter.admit("1.2.3.4", 2, 1_800)

    assert limiter.admit("1.2.3.4", 2, _HOUR - 1).allowed is False
    assert limiter.admit("1.2.3.4", 2, _HOUR).allowed is True
    assert limiter.admit("1.2.3.4", 2, _HOUR + 1).allowed is False


def test_clients_are_counted_separately():
    limiter = SlidingWindowRateLimiter(window_seconds=_HOUR)
    limiter.admit("1.2.3.4", 1, 0)

    assert limiter.admit("5.6.7.8", 1, 1).allowed is True
