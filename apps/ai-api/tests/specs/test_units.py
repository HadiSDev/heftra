"""Line units read as pricing units."""
from __future__ import annotations

from decimal import Decimal

from web_api.db.models import PricingUnit
from web_api.specs.units import line_unit, units_per_line_unit


def test_danish_and_english_units_are_known():
    assert line_unit("Stk") == (PricingUnit.PIECE, Decimal(1))
    assert line_unit("ruller") == (PricingUnit.ROLL, Decimal(1))
    assert line_unit(" kasse ") == (PricingUnit.PACK, Decimal(1))
    assert line_unit("mm") == (PricingUnit.M, Decimal("0.001"))
    assert line_unit("kvm") == (PricingUnit.M2, Decimal(1))
    assert line_unit("bundle") is None
    assert line_unit(None) is None


def test_a_stated_pack_size_wins():
    assert units_per_line_unit("stk", PricingUnit.ROLL, 8) == Decimal(8)


def test_a_line_unit_of_another_pricing_unit_gives_no_pack_size():
    assert units_per_line_unit("stk", PricingUnit.M, None) is None
    assert units_per_line_unit("cm", PricingUnit.M, None) == Decimal("0.01")
