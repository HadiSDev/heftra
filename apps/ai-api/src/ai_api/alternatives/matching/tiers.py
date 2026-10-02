"""Parts sold in ranked lines: a lower tier is worse whatever its generation, and an older
generation is worse within a tier."""
from __future__ import annotations

import re
from dataclasses import dataclass

from web_api.specs.attribute import Attribute

from .verdicts import Verdict

FAMILIES: dict[str, list[str]] = {
    "intel core": ["i3", "i5", "i7", "i9"],
    "intel core ultra": ["5", "7", "9"],
    "amd ryzen": ["3", "5", "7", "9"],
    "apple m": ["", "pro", "max", "ultra"],
    "en 10025": ["s235", "s275", "s355", "s420", "s460"],
}

_INTEL_CORE = re.compile(r"\bi([3579])[\s-]*(\d{4,5})", re.I)
_CORE_ULTRA = re.compile(r"\bultra\s*([579])\s*(\d)\d{2}", re.I)
_RYZEN = re.compile(r"\bryzen\s*([3579])\s*(?:pro\s*)?(\d)\d{3}", re.I)
_APPLE_M = re.compile(r"\bm(\d)\s*(pro|max|ultra)?\b", re.I)
_STEEL = re.compile(r"\bs\s*(235|275|355|420|460)", re.I)


@dataclass(frozen=True)
class TierPart:
    family: str
    rank: int
    generation: int | None


def parse_part(attribute: Attribute) -> TierPart | None:
    """The family, rank and generation of a tiered attribute, from its value first and its
    stated family, tier and generation otherwise; None when it is in no known family."""
    return _from_value(f"{attribute.family or ''} {attribute.value}") or _from_fields(attribute)


def compare_tiers(item: Attribute, candidate: Attribute) -> Verdict | None:
    """Same, better or worse when both parts are in the same known family; None when the table
    can't place them, for the LLM to decide."""
    mine = parse_part(item)
    theirs = parse_part(candidate)
    if mine is None or theirs is None or mine.family != theirs.family:
        return None
    if theirs.rank < mine.rank:
        return Verdict.WORSE
    if mine.generation is not None:
        if theirs.generation is None:
            return None
        if theirs.generation < mine.generation:
            return Verdict.WORSE
    if theirs.rank == mine.rank and theirs.generation == mine.generation:
        return Verdict.SAME
    return Verdict.BETTER


def _from_value(text: str) -> TierPart | None:
    lowered = text.lower()
    if "ultra" in lowered and (found := _CORE_ULTRA.search(text)):
        return _part("intel core ultra", found.group(1), int(found.group(2)))
    if found := _INTEL_CORE.search(text):
        return _part("intel core", f"i{found.group(1)}", _intel_generation(found.group(2)))
    if found := _RYZEN.search(text):
        return _part("amd ryzen", found.group(1), int(found.group(2)))
    if "apple" in lowered or re.search(r"\bm\d\b", lowered):
        if found := _APPLE_M.search(text):
            return _part("apple m", (found.group(2) or "").lower(), int(found.group(1)))
    if found := _STEEL.search(text):
        return _part("en 10025", f"s{found.group(1)}", None)
    return None


def _from_fields(attribute: Attribute) -> TierPart | None:
    family = " ".join((attribute.family or "").lower().split())
    if family not in FAMILIES or attribute.tier is None:
        return None
    tier = attribute.tier.strip().lower().removeprefix(family).strip()
    generation = int(attribute.generation) if (attribute.generation or "").isdigit() else None
    return _part(family, tier, generation)


def _part(family: str, tier: str, generation: int | None) -> TierPart | None:
    tiers = FAMILIES[family]
    if tier not in tiers:
        return None
    return TierPart(family, tiers.index(tier), generation)


def _intel_generation(model: str) -> int:
    """i7-1355U is the 13th generation, i7-8565U the 8th, i9-13900K the 13th."""
    if len(model) == 5 or model.startswith("1"):
        return int(model[:2])
    return int(model[0])
