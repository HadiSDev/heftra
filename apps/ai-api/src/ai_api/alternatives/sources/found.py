"""A candidate a source found for an item, priced per the item's pricing unit."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from web_api.db.models import AlternativeMatch, AlternativeSource, CompanyItem

from ...specs.specification import Specification


@dataclass(frozen=True)
class ItemContext:
    """The item being searched, with what every source needs to know of it."""

    item: CompanyItem
    spec: Specification
    organization_id: str
    base_currency: str
    eur_rate: Decimal | None


@dataclass(frozen=True)
class Found:
    """`unit_price` is per the item's pricing unit, without VAT, in its base currency. `match`
    is set when the source already knows it; otherwise `spec` is matched. `vendor_id` or
    `seller_host` name who sells it, for agreement checks."""

    source: AlternativeSource
    ref_key: str
    name: str
    unit_price: Decimal
    origin: dict
    spec: Specification | None = None
    product_id: str | None = None
    match: AlternativeMatch | None = None
    vendor_id: str | None = None
    seller_host: str | None = None
