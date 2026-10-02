"""The size an item states in its own text ("10g", "250 ml", "305m"), as a pack size in its
pricing unit, for when the reader left it out."""
from __future__ import annotations

import re
from decimal import Decimal

from web_api.db.models import PricingUnit
from web_api.specs.specification import Specification
from web_api.specs.units import line_unit

_SIZE = re.compile(r"(?<![\w.,])(\d+(?:[.,]\d+)?)\s*(kg|mg|g|ml|cl|dl|l|mm|cm|m)\b(?!\s*/)",
                   re.I)
_MEASURES: dict[str, tuple[PricingUnit, Decimal]] = {
    "kg": (PricingUnit.KG, Decimal(1)), "g": (PricingUnit.KG, Decimal("0.001")),
    "mg": (PricingUnit.KG, Decimal("0.000001")),
    "l": (PricingUnit.L, Decimal(1)), "dl": (PricingUnit.L, Decimal("0.1")),
    "cl": (PricingUnit.L, Decimal("0.01")), "ml": (PricingUnit.L, Decimal("0.001")),
    "m": (PricingUnit.M, Decimal(1)), "cm": (PricingUnit.M, Decimal("0.01")),
    "mm": (PricingUnit.M, Decimal("0.001")),
}


def stated_size(texts: list[str | None], pricing_unit: PricingUnit) -> Decimal | None:
    """The first size in the texts measured in the pricing unit's dimension, converted to it."""
    for text in texts:
        for amount, unit in _SIZE.findall(text or ""):
            measure = _MEASURES.get(unit.lower())
            if measure is not None and measure[0] == pricing_unit:
                return Decimal(amount.replace(",", ".")) * measure[1]
    return None


def with_stated_size(spec: Specification, line_unit_text: str | None,
                     texts: list[str | None]) -> Specification:
    """The specification with the pack size its item states, when it is priced by a measure,
    the reader gave none or one, and the line isn't bought in that measure already."""
    if spec.pricing_unit not in (PricingUnit.KG, PricingUnit.L, PricingUnit.M):
        return spec
    if spec.units_per_line_unit not in (None, 1.0):
        return spec
    bought_in = line_unit(line_unit_text)
    if bought_in is not None and bought_in[0] == spec.pricing_unit:
        return spec
    size = stated_size([line_unit_text, *texts], spec.pricing_unit)
    if size is None or size == 1:
        return spec
    return spec.model_copy(update={"units_per_line_unit": float(size)})
