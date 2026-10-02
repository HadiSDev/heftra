"""An item's quantity in its pricing unit and its price per pricing unit."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from ..db.models import CompanyItem

from .specification import read_spec
from .units import units_per_line_unit

PRICE_PLACES = Decimal("0.000001")


class PriceNote(str, Enum):
    """Why an item has no price per pricing unit."""

    NOT_BOUGHT = "not_bought"
    NO_SPECIFICATION = "no_specification"
    NO_PACK_SIZE = "no_pack_size"
    NO_QUANTITY = "no_quantity"


def price_item(item: CompanyItem, eur_rate: Decimal | None) -> None:
    """Set the item's yearly quantity and unit price from its lines and specification, in base
    currency and in EUR at `eur_rate`, or say why it has none."""
    item.quantity = None
    item.unit_price = None
    item.unit_price_eur = None
    note = _missing(item)
    item.price_note = note.value if note is not None else None
    if note is not None:
        return
    spec = read_spec(item.spec)
    per = units_per_line_unit(item.unit, spec.pricing_unit, spec.units_per_line_unit)
    item.quantity = item.line_quantity * per
    item.unit_price = (item.priced_spend / item.quantity).quantize(PRICE_PLACES, ROUND_HALF_UP)
    if eur_rate is not None:
        item.unit_price_eur = (item.unit_price * eur_rate).quantize(PRICE_PLACES, ROUND_HALF_UP)


def _missing(item: CompanyItem) -> PriceNote | None:
    if item.lines == 0:
        return PriceNote.NOT_BOUGHT
    spec = read_spec(item.spec)
    if spec is None:
        return PriceNote.NO_SPECIFICATION
    if units_per_line_unit(item.unit, spec.pricing_unit, spec.units_per_line_unit) is None:
        return PriceNote.NO_PACK_SIZE
    if not item.line_quantity or not item.priced_spend:
        return PriceNote.NO_QUANTITY
    return None
