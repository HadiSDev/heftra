"""Product identifiers in one form, so the same product compares equal from any source."""
from __future__ import annotations

import re

_SEPARATORS = re.compile(r"[\s\-_.]+")
_GTIN_LENGTHS = (8, 12, 13, 14)


def part_number(text: str | None) -> str | None:
    """A manufacturer part number, upper case, without spaces, hyphens, dots or underscores."""
    if not text:
        return None
    normal = _SEPARATORS.sub("", text).upper()
    return normal or None


def gtin(text: str | None) -> str | None:
    """An EAN/UPC/GTIN as 14 digits, or None when it isn't one."""
    if not text:
        return None
    digits = re.sub(r"\D", "", text)
    if len(digits) not in _GTIN_LENGTHS or not _check_digit_ok(digits):
        return None
    return digits.zfill(14)


def brand(text: str | None) -> str | None:
    if not text:
        return None
    normal = " ".join(text.lower().split())
    return normal or None


def model(text: str | None) -> str | None:
    if not text:
        return None
    normal = " ".join(_SEPARATORS.sub(" ", text).lower().split())
    return normal or None


def _check_digit_ok(digits: str) -> bool:
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(digit) * (3 if index % 2 == 0 else 1)
                for index, digit in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check
