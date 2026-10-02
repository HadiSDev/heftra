"""Numeric attributes compared in one unit, by which way is better."""
from __future__ import annotations

from web_api.specs.attribute import Attribute, Direction

from .verdicts import Verdict

_UNITS: dict[str, tuple[str, float]] = {
    "mm": ("length", 0.001), "cm": ("length", 0.01), "m": ("length", 1.0),
    "km": ("length", 1000.0), "in": ("length", 0.0254), "inch": ("length", 0.0254),
    "\"": ("length", 0.0254), "tommer": ("length", 0.0254),
    "g": ("mass", 0.001), "kg": ("mass", 1.0), "t": ("mass", 1000.0),
    "mb": ("data", 0.001), "gb": ("data", 1.0), "tb": ("data", 1000.0),
    "w": ("power", 1.0), "kw": ("power", 1000.0),
    "v": ("voltage", 1.0), "kv": ("voltage", 1000.0),
    "ml": ("volume", 0.001), "cl": ("volume", 0.01), "l": ("volume", 1.0),
    "mm2": ("area", 1e-6), "cm2": ("area", 1e-4), "m2": ("area", 1.0),
    "mhz": ("frequency", 0.001), "ghz": ("frequency", 1.0),
    "mah": ("charge", 1.0), "ah": ("charge", 1000.0),
}


def in_base_unit(number: float, unit: str | None) -> tuple[str, float] | None:
    """The number in its dimension's base unit; a unit the table doesn't know is its own
    dimension."""
    if unit is None or not unit.strip():
        return ("", number)
    key = unit.strip().lower().replace("²", "2").replace(" ", "")
    known = _UNITS.get(key)
    if known is None:
        return (key, number)
    return (known[0], number * known[1])


def compare_numbers(item: Attribute, candidate: Attribute,
                    tolerance_percent: float) -> Verdict | None:
    """Same, better or worse by the item's direction; None when they can't be compared in code
    (no number, or units of different dimensions)."""
    if item.number is None or candidate.number is None:
        return None
    mine = in_base_unit(item.number, item.unit)
    theirs = in_base_unit(candidate.number, candidate.unit)
    if mine[0] != theirs[0]:
        return None
    if _close(mine[1], theirs[1], tolerance_percent):
        return Verdict.SAME
    if item.direction == Direction.EQUAL:
        return Verdict.WORSE
    more = theirs[1] > mine[1]
    return Verdict.BETTER if more == (item.direction == Direction.MORE) else Verdict.WORSE


def _close(mine: float, theirs: float, tolerance_percent: float) -> bool:
    if mine == 0:
        return theirs == 0
    return abs(theirs - mine) / abs(mine) * 100 <= tolerance_percent
