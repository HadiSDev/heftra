"""Finding catalog entries by what the stored rows carry."""
from __future__ import annotations

from .milestones import MILESTONES
from .shapes import ProductSpec
from .suppliers import SUPPLIERS


def products_by_name() -> dict[str, ProductSpec]:
    """Every product sold or invoiced as a milestone, by the item name its lines carry."""
    products = {offer.product.name: offer.product
                for supplier in SUPPLIERS for offer in supplier.offers}
    products.update({milestone.product.name: milestone.product for milestone in MILESTONES})
    return products


def sector_codes() -> set[str]:
    return {product.sector for product in products_by_name().values()}
