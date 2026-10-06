"""Why each line got its category and emission sector, as the models would have put it."""
from __future__ import annotations

from decimal import Decimal

from web_api.db.models import EmissionSector, SpendCategory

from ...catalog.shapes import ProductSpec, SupplierSpec

REVIEW_BELOW = Decimal("0.6")


def category_rationale(product: ProductSpec, supplier: SupplierSpec, leaf: SpendCategory,
                       confidence: Decimal) -> str:
    if confidence < REVIEW_BELOW:
        return (f"The line names {product.name.lower()} without saying which project or use it "
                f"is for; {leaf.name} is the closest category, but it could also be booked as "
                f"site overhead.")
    return (f"'{product.name}' from {supplier.name} is {leaf.description}, which is what "
            f"{leaf.level_2} › {leaf.name} covers.")


def sector_rationale(product: ProductSpec, sector: EmissionSector) -> str:
    return (f"{product.name} is produced or delivered by the "
            f"{sector.name[0].lower()}{sector.name[1:]} sector.")
