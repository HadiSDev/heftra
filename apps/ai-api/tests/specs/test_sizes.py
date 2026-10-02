"""Sizes an item states, used as its pack size when the reader left it at one."""
from __future__ import annotations

from decimal import Decimal

from ai_api.specs.sizes import stated_size, with_stated_size
from spec_stub import spec
from web_api.db.models import PricingUnit
from web_api.specs.specification import Specification


def _spec(**fields) -> Specification:
    return Specification.model_validate(spec("x", item_class="material", **fields))


def test_sizes_in_the_pricing_units_dimension():
    assert stated_size(["THERMAL HERO 10g"], PricingUnit.KG) == Decimal("0.010")
    assert stated_size(["Konzentrat, 250ml"], PricingUnit.L) == Decimal("0.250")
    assert stated_size(["Cat6 305m kasse"], PricingUnit.M) == Decimal("305")
    assert stated_size(["Rundstål S235 20mm"], PricingUnit.KG) is None


def test_a_rate_is_not_a_size():
    assert stated_size(["Kopipapir A4 80 g / m²"], PricingUnit.KG) is None


def test_a_tube_priced_per_kg_gets_its_size():
    corrected = with_stated_size(_spec(pricing_unit="kg", units_per_line_unit=1), "stk",
                                 ["THERMAL HERO Wärmeleitpaste - 10g", None])
    assert corrected.units_per_line_unit == 0.01


def test_a_line_bought_by_the_measure_keeps_one():
    kept = with_stated_size(_spec(pricing_unit="kg", units_per_line_unit=1), "kg",
                            ["Rundstål 6m 20mm"])
    assert kept.units_per_line_unit == 1


def test_a_stated_pack_size_is_kept():
    kept = with_stated_size(_spec(pricing_unit="m", units_per_line_unit=100), "stk",
                            ["Cat6 305m kasse"])
    assert kept.units_per_line_unit == 100
