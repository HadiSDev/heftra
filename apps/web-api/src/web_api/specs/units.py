"""The units lines are bought in, mapped to the pricing units specifications use."""
from __future__ import annotations

from decimal import Decimal

from ..db.models import PricingUnit

LINE_UNITS: dict[str, tuple[PricingUnit, Decimal]] = {
    **{word: (PricingUnit.PIECE, Decimal(1)) for word in (
        "stk", "stk.", "styk", "styks", "pcs", "pc", "piece", "pieces", "ea", "each", "st",
        "unit", "units")},
    **{word: (PricingUnit.KG, Decimal(1)) for word in ("kg", "kilo", "kilogram", "kgs")},
    "g": (PricingUnit.KG, Decimal("0.001")),
    "gram": (PricingUnit.KG, Decimal("0.001")),
    "t": (PricingUnit.KG, Decimal(1000)),
    "ton": (PricingUnit.KG, Decimal(1000)),
    "tons": (PricingUnit.KG, Decimal(1000)),
    **{word: (PricingUnit.M, Decimal(1)) for word in (
        "m", "meter", "metre", "meters", "metres", "mtr", "lbm", "lb.m")},
    "cm": (PricingUnit.M, Decimal("0.01")),
    "mm": (PricingUnit.M, Decimal("0.001")),
    **{word: (PricingUnit.M2, Decimal(1)) for word in ("m2", "m²", "kvm", "sqm")},
    **{word: (PricingUnit.M3, Decimal(1)) for word in ("m3", "m³", "kbm", "cbm")},
    **{word: (PricingUnit.L, Decimal(1)) for word in ("l", "ltr", "liter", "litre", "liters")},
    "ml": (PricingUnit.L, Decimal("0.001")),
    "cl": (PricingUnit.L, Decimal("0.01")),
    **{word: (PricingUnit.ROLL, Decimal(1)) for word in ("rulle", "ruller", "rl", "roll", "rolls")},
    **{word: (PricingUnit.SHEET, Decimal(1)) for word in ("ark", "sheet", "sheets")},
    **{word: (PricingUnit.PACK, Decimal(1)) for word in (
        "pk", "pk.", "pkt", "pakke", "pakker", "pack", "packs", "ks", "kasse", "box", "boks")},
}


def line_unit(unit: str | None) -> tuple[PricingUnit, Decimal] | None:
    """The pricing unit a line's unit is, and how many of it one line unit is."""
    if not unit:
        return None
    return LINE_UNITS.get(" ".join(unit.strip().lower().split()))


def units_per_line_unit(line: str | None, pricing_unit: PricingUnit,
                        stated: float | None) -> Decimal | None:
    """How many pricing units one unit of the line holds: what the specification states, or
    what the line's own unit converts to when it is that pricing unit."""
    if stated is not None:
        return Decimal(str(stated))
    known = line_unit(line)
    if known is not None and known[0] == pricing_unit:
        return known[1]
    return None
