"""Whether a candidate is the item itself: the same product, EAN, part number, or make and
model with nothing that differs."""
from __future__ import annotations

from ...specs import identifiers
from ...specs.attribute import Attribute
from ...specs.specification import Specification


def is_exact(item: Specification, item_product: str | None, candidate: Specification,
             candidate_product: str | None) -> bool:
    if item_product is not None and item_product == candidate_product:
        return True
    gtin = identifiers.gtin(item.gtin)
    if gtin is not None and gtin == identifiers.gtin(candidate.gtin):
        return True
    part = identifiers.part_number(item.part_number)
    if part is not None and part == identifiers.part_number(candidate.part_number) \
            and _brands_agree(item, candidate):
        return True
    model = identifiers.model(item.model)
    return (model is not None and model == identifiers.model(candidate.model)
            and identifiers.brand(item.brand) is not None
            and identifiers.brand(item.brand) == identifiers.brand(candidate.brand)
            and _same_attributes(item.attributes, candidate.attributes))


def _brands_agree(item: Specification, candidate: Specification) -> bool:
    mine = identifiers.brand(item.brand)
    theirs = identifiers.brand(candidate.brand)
    return mine is None or theirs is None or mine == theirs


def _same_attributes(mine: list[Attribute], theirs: list[Attribute]) -> bool:
    """Every attribute both state says the same, so one model in two configurations isn't
    taken for one product."""
    stated = {attribute.name: _value(attribute) for attribute in theirs}
    return all(stated.get(attribute.name, _value(attribute)) == _value(attribute)
               for attribute in mine)


def _value(attribute: Attribute) -> str:
    if attribute.number is not None:
        return f"{attribute.number:g} {(attribute.unit or '').lower()}".strip()
    return " ".join(attribute.value.lower().split())
