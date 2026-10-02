"""An item: what a company bought, from one supplier, over all the lines that bought it."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .keys import item_text


@dataclass(frozen=True)
class Item:
    key: str
    item_name: str | None
    description: str | None
    unit: str | None
    category_id: str | None
    category_path: tuple[str, ...]
    vendor_id: str | None
    vendor_name: str | None
    lines: int
    spend: Decimal
    unit_price: Decimal | None
    first_on: date | None
    last_on: date | None

    @property
    def text(self) -> str:
        """What the item is, with its category, for similarity search."""
        category = " / ".join(self.category_path)
        name = item_text(self.item_name, self.description)
        return f"{name} — {category}" if category else name
