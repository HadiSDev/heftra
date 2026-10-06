"""Recognising demo requests sent by bots rather than people."""
from __future__ import annotations

MINIMUM_FILL_MILLISECONDS = 3_000


def is_automated_submission(website: str | None, rendered_at_ms: int, now_ms: int) -> bool:
    """A filled honeypot, or a form submitted faster than a person can fill it in."""
    if website:
        return True
    return now_ms - rendered_at_ms < MINIMUM_FILL_MILLISECONDS
