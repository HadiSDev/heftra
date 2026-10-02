"""Candidates matched to an item: exact, equivalent, or rejected; the LLM asked once per pair."""
from __future__ import annotations

import json
import re

import pytest
from sqlmodel import Session

from ai_api.alternatives.matching.judge import PairJudge
from ai_api.alternatives.matching.matcher import Candidate, match_candidates
from spec_stub import spec
from web_api.specs.specification import Specification

_CANDIDATES = re.compile(r"^Candidate (\d+):\nProduct type: (.*)$", re.M)


def _spec(name: str, **fields) -> Specification:
    return Specification.model_validate(spec(name, **fields))


def memory(gb: int) -> dict:
    return {"name": "memory", "kind": "numeric", "value": f"{gb} GB", "number": gb, "unit": "GB",
            "direction": "more"}


def cpu(value: str) -> dict:
    return {"name": "processor", "kind": "tiered", "value": value}


class Comparer:
    """Says a candidate is the same kind unless its type names a tablet, and every attribute
    asked the same; counts prompts."""

    def __init__(self) -> None:
        self.prompts = 0

    def __call__(self, prompt: str) -> str:
        self.prompts += 1
        answers = []
        for number, kind in _CANDIDATES.findall(prompt):
            asked = re.search(rf"Candidate {number}:.*?Attributes to compare: (.*?)$", prompt,
                              re.S | re.M).group(1)
            names = [] if asked == "(none)" else asked.split(", ")
            answers.append({"n": int(number), "same_kind": "tablet" not in kind,
                            "kind_reason": "A tablet is not a laptop.",
                            "attributes": [{"name": name, "verdict": "same", "reason": "ok"}
                                           for name in names]})
        return json.dumps({"candidates": answers})


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


LAPTOP = _spec("ThinkPad T14", brand="Lenovo", part_number="21ML003XMX",
               attributes=[cpu("Intel Core i7-1355U"), memory(16)])


def _match(session, comparer, *candidates: Candidate):
    return match_candidates(LAPTOP, None, list(candidates), PairJudge(session, comparer))


def test_the_same_part_number_is_exact(session):
    results = _match(session, Comparer(), Candidate("c", _spec("T14", part_number="21ML-003XMX",
                                                                  brand="Lenovo"), None))
    assert results["c"].match.value == "exact"


def test_lower_tiers_and_less_memory_are_rejected_without_asking(session):
    comparer = Comparer()
    results = _match(
        session, comparer,
        Candidate("i3", _spec("Laptop", attributes=[cpu("Intel Core i3-1315U"), memory(16)]), None),
        Candidate("i5", _spec("Laptop", attributes=[cpu("Intel Core i5-1435U"), memory(32)]), None),
        Candidate("old", _spec("Laptop", attributes=[cpu("Intel Core i7-1165G7"), memory(16)]),
                  None),
        Candidate("8gb", _spec("Laptop", attributes=[cpu("Intel Core i7-1365U"), memory(8)]), None),
    )

    assert all(not result.accepted for result in results.values())
    assert comparer.prompts == 0


def test_an_equal_or_better_laptop_is_equivalent_without_asking(session):
    comparer = Comparer()
    results = _match(session, comparer, Candidate(
        "c", _spec("Laptop", attributes=[cpu("Intel Core i7-1365U"), memory(32)]), None))

    assert results["c"].match.value == "equivalent"
    assert [entry.verdict.value for entry in results["c"].comparison] == ["same", "better"]
    assert comparer.prompts == 0


def test_another_family_is_asked_once_per_pair(session):
    comparer = Comparer()
    ryzen = Candidate("c", _spec("Laptop", attributes=[cpu("AMD Ryzen 7 7730U"), memory(16)]),
                      None)

    first = _match(session, comparer, ryzen)
    second = _match(session, comparer, ryzen)

    assert first["c"].match.value == "equivalent" and second["c"].accepted
    assert comparer.prompts == 1


def test_a_tablet_is_another_kind_of_product(session):
    results = _match(session, Comparer(), Candidate(
        "c", _spec("Tablet", product_type="2-in-1 tablet",
                   attributes=[cpu("Intel Core i7-1365U"), memory(16)]), None))

    assert not results["c"].accepted
    assert "another kind" in results["c"].rejected


def test_a_missing_attribute_is_not_assumed(session):
    def says_missing(prompt: str) -> str:
        return json.dumps({"candidates": [{"n": 1, "same_kind": True, "attributes": [
            {"name": "memory", "verdict": "missing", "reason": "Not stated."}]}]})

    results = _match(session, says_missing, Candidate(
        "c", _spec("Laptop", attributes=[cpu("Intel Core i7-1365U")]), None))

    assert not results["c"].accepted


def test_a_better_steel_grade_is_equivalent(session):
    bar = {"item_class": "material", "product_type": "hot-rolled round bar", "pricing_unit": "kg"}
    item = _spec("Round bar", **bar, attributes=[
        {"name": "steel_grade", "kind": "tiered", "value": "S235JR"},
        {"name": "diameter", "kind": "numeric", "value": "20 mm", "number": 20, "unit": "mm",
         "direction": "equal"}])
    candidate = _spec("Round bar", **bar, attributes=[
        {"name": "grade", "kind": "tiered", "value": "S355J2"},
        {"name": "diameter", "kind": "numeric", "value": "20 mm", "number": 20, "unit": "mm",
         "direction": "equal"}])

    results = match_candidates(item, None, [Candidate("c", candidate, None)],
                               PairJudge(session, Comparer()))

    assert results["c"].match.value == "equivalent"
    assert results["c"].comparison[0].verdict.value == "better"
