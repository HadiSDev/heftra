"""Numbers compared in one unit by which way is better."""
from __future__ import annotations

from ai_api.alternatives.matching.numbers import compare_numbers
from ai_api.alternatives.matching.verdicts import Verdict
from ai_api.specs.attribute import Attribute


def number(value: float, unit: str | None, direction: str = "more") -> Attribute:
    return Attribute(name="x", kind="numeric", value=f"{value} {unit}", number=value, unit=unit,
                     direction=direction)


def test_less_memory_is_worse():
    assert compare_numbers(number(16, "GB"), number(8, "GB"), 2) == Verdict.WORSE
    assert compare_numbers(number(16, "GB"), number(32, "GB"), 2) == Verdict.BETTER


def test_units_are_converted():
    assert compare_numbers(number(512, "GB"), number(1, "TB"), 2) == Verdict.BETTER
    assert compare_numbers(number(20, "mm", "equal"), number(2, "cm", "equal"), 2) == Verdict.SAME


def test_a_size_that_must_match_allows_the_tolerance_only():
    assert compare_numbers(number(14, "in", "equal"), number(14.2, "in", "equal"), 2) == Verdict.SAME
    assert compare_numbers(number(14, "in", "equal"), number(16, "in", "equal"), 2) == Verdict.WORSE


def test_less_is_better_for_weight():
    assert compare_numbers(number(1.4, "kg", "less"), number(1200, "g", "less"), 2) == Verdict.BETTER


def test_different_dimensions_are_left_to_the_llm():
    assert compare_numbers(number(16, "GB"), number(16, "W"), 2) is None
