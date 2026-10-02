"""An item a company buys, with its specification, price and alternatives."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from web_api.db.models import ItemClass, SpecSource
from web_api.specs.specification import Specification

from ..common import Page
from .alternatives import AlternativeRead


class ItemSummary(BaseModel):
    """An item in the Alternatives list, with its best open alternative."""

    id: str
    company_id: str
    name: str
    supplier_name: str | None = None
    item_class: ItemClass | None = None
    pricing_unit: str | None = None
    unit_price: Decimal | None = None
    quantity: Decimal | None = None
    currency: str | None = None
    alternatives: int
    best: AlternativeRead | None = None


class AlternativesPage(Page[ItemSummary]):
    """`total_saving` adds up the listed items' best yearly savings, when they share a
    currency; `searched_items` is how many of the companies' items have been searched, so an
    empty list can say whether nothing was searched or nothing cheaper was found."""

    total_saving: Decimal | None = None
    currency: str | None = None
    searched_items: int = 0


class ItemRead(BaseModel):
    """`price_note` says why there is no unit price: not_bought, no_specification,
    no_pack_size or no_quantity."""

    id: str
    company_id: str
    item_name: str | None = None
    description: str | None = None
    unit: str | None = None
    vendor_id: str | None = None
    supplier_name: str | None = None
    category_path: list[str] = []
    spec: Specification | None = None
    spec_source: SpecSource | None = None
    spend: Decimal
    lines: int
    last_bought_on: date | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    currency: str | None = None
    price_note: str | None = None
    searched_at: datetime | None = None
    searching: bool = False
    alternatives: list[AlternativeRead] = []
