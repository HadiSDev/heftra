"""Identifiers normalised so the same product compares equal."""
from __future__ import annotations

from ai_api.specs import identifiers


def test_part_numbers_lose_their_separators():
    assert identifiers.part_number(" 21ml-003xmx ") == "21ML003XMX"
    assert identifiers.part_number("MXK73DK/A") == "MXK73DK/A"


def test_a_gtin_needs_its_check_digit():
    assert identifiers.gtin("4006381333931") == "04006381333931"
    assert identifiers.gtin("40 0638 1333 931") == "04006381333931"
    assert identifiers.gtin("4006381333932") is None
    assert identifiers.gtin("12345") is None
