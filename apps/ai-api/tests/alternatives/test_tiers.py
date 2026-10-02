"""Ranked parts: a lower tier is never an alternative, nor an older generation of a tier."""
from __future__ import annotations

from ai_api.alternatives.matching.tiers import compare_tiers, parse_part
from ai_api.alternatives.matching.verdicts import Verdict
from web_api.specs.attribute import Attribute


def cpu(value: str, **fields) -> Attribute:
    return Attribute(name="processor", kind="tiered", value=value, **fields)


def test_intel_parts_are_parsed_with_their_generation():
    assert parse_part(cpu("Intel Core i7-1355U")).generation == 13
    assert parse_part(cpu("Intel Core i7-8565U")).generation == 8
    assert parse_part(cpu("Core i9-13900K")).generation == 13
    assert parse_part(cpu("Core i5-1135G7")).generation == 11


def test_a_lower_tier_is_worse_even_when_newer():
    i7 = cpu("Intel Core i7-1355U")
    assert compare_tiers(i7, cpu("Intel Core i3-1315U")) == Verdict.WORSE
    assert compare_tiers(i7, cpu("Intel Core i5-1435U")) == Verdict.WORSE
    assert compare_tiers(i7, cpu("Intel Core i5-14500")) == Verdict.WORSE


def test_an_older_generation_of_the_tier_is_worse():
    assert compare_tiers(cpu("Intel Core i7-1355U"), cpu("Intel Core i7-1165G7")) == Verdict.WORSE


def test_the_same_or_a_higher_part_is_not_worse():
    i7 = cpu("Intel Core i7-1355U")
    assert compare_tiers(i7, cpu("Core i7-1365U")) == Verdict.SAME
    assert compare_tiers(i7, cpu("Intel Core i9-13900H")) == Verdict.BETTER
    assert compare_tiers(i7, cpu("Intel Core i7-1455U")) == Verdict.BETTER


def test_another_family_is_left_to_the_llm():
    assert compare_tiers(cpu("Intel Core i7-1355U"), cpu("AMD Ryzen 7 7730U")) is None
    assert compare_tiers(cpu("Intel Core i7-1355U"), cpu("Intel Core Ultra 7 155U")) is None


def test_other_families():
    assert compare_tiers(cpu("AMD Ryzen 7 7730U"), cpu("AMD Ryzen 5 7530U")) == Verdict.WORSE
    assert compare_tiers(cpu("Intel Core Ultra 7 155U"),
                         cpu("Intel Core Ultra 5 125U")) == Verdict.WORSE
    assert compare_tiers(cpu("Apple M3 Pro"), cpu("Apple M3")) == Verdict.WORSE
    assert compare_tiers(cpu("Apple M3"), cpu("Apple M4")) == Verdict.BETTER


def test_steel_grades():
    grade = Attribute(name="steel_grade", kind="tiered", value="S235JR")
    assert compare_tiers(grade, Attribute(name="steel_grade", kind="tiered",
                                          value="S355J2")) == Verdict.BETTER
    assert compare_tiers(Attribute(name="steel_grade", kind="tiered", value="S355J2"),
                         grade) == Verdict.WORSE


def test_stated_fields_are_used_when_the_value_says_little():
    stated = cpu("Ultra", family="Intel Core Ultra", tier="7", generation="1")
    assert parse_part(stated).rank == 1
