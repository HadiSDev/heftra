"""Linking an item to the product it is, by its EAN or its maker's part number."""
from __future__ import annotations

from sqlmodel import Session, select

from web_api.db.models import Product
from web_api.specs.specification import Specification

from . import identifiers


def link_product(session: Session, spec: Specification) -> Product | None:
    """The product the specification identifies, created when first seen; None when it states
    neither an EAN nor a part number."""
    gtin = identifiers.gtin(spec.gtin)
    part = identifiers.part_number(spec.part_number)
    brand = identifiers.brand(spec.brand)
    if gtin is None and part is None:
        return None
    found = _by_gtin(session, gtin) or _by_part(session, part, brand)
    if found is not None:
        if found.gtin is None and gtin is not None:
            found.gtin = gtin
            session.add(found)
        return found
    product = Product(gtin=gtin, brand=brand, part_number=part,
                      model=identifiers.model(spec.model), name=spec.name,
                      item_class=spec.item_class.value, pricing_unit=spec.pricing_unit.value)
    session.add(product)
    session.flush()
    return product


def _by_gtin(session: Session, gtin: str | None) -> Product | None:
    if gtin is None:
        return None
    return session.exec(select(Product).where(Product.gtin == gtin)).first()


def _by_part(session: Session, part: str | None, brand: str | None) -> Product | None:
    """A product with the part number and the same brand, or with no brand on either side."""
    if part is None:
        return None
    for product in session.exec(select(Product).where(Product.part_number == part)).all():
        if product.brand is None or brand is None or product.brand == brand:
            return product
    return None
