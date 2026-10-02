"""The prompt comparing an item's candidates with it."""
from __future__ import annotations

from web_api.specs.attribute import Attribute, AttributeKind
from web_api.specs.specification import Specification

from ...parsing import json_format_hint
from .questions import Answers, Question

_RULES = [
    "A company wants a cheaper product that can replace what it buys. A candidate may replace "
    "the item only when it is the same kind of product for the same use and is not worse on "
    "any of the item's key attributes.",
    "same_kind (when asked): true only for the same kind of product used the same way. A "
    "gaming laptop or a tablet is not a business laptop; a flat bar is not a round bar; a "
    "Cat5e cable is not a Cat6 cable.",
    "For each attribute asked, find the candidate's matching attribute (it may be named "
    "differently) and answer \"same\", \"better\" (better for the buyer's purpose), \"worse\" "
    "or \"missing\" (the candidate doesn't state it).",
    "Ranked parts (processors, graphics cards, material grades): a lower tier is always worse, "
    "even when it is newer, so a Core i5 or i3 never replaces a Core i7 and a Ryzen 5 never "
    "replaces a Ryzen 7. An older generation of the same tier is worse. Across makers, only a "
    "part of the same performance class and age is \"same\". When unsure, answer \"worse\".",
    "Give one short reason for each answer.",
]


def compare_prompt(item: Specification, questions: list[Question]) -> str:
    lines = [*_RULES, "", "The item:", *_spec_lines(item), ""]
    for number, question in enumerate(questions, start=1):
        asked = ", ".join(question.attributes) or "(none)"
        lines += [f"Candidate {number}:", *_spec_lines(question.candidate),
                  f"Ask same_kind: {'yes' if question.ask_kind else 'no'}",
                  f"Attributes to compare: {asked}", ""]
    lines.append(json_format_hint(Answers))
    return "\n".join(lines)


def _spec_lines(spec: Specification) -> list[str]:
    identity = ", ".join(part for part in (spec.brand, spec.model, spec.part_number) if part)
    return [f"Product type: {spec.product_type}", f"Name: {spec.name}",
            *([f"Identifiers: {identity}"] if identity else []),
            "Attributes: " + ("; ".join(_attribute(attribute) for attribute in spec.attributes)
                              or "(none stated)")]


def _attribute(attribute: Attribute) -> str:
    if attribute.kind == AttributeKind.NUMERIC and attribute.number is not None:
        return f"{attribute.name} = {attribute.number:g} {attribute.unit or ''}".strip()
    return f"{attribute.name} = {attribute.value}"
