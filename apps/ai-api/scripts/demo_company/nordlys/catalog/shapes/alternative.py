"""A cheaper alternative to one of the demo company's items, as a search would have found it."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlternativeSpec:
    """The item is `product` bought from `supplier`. A history alternative is the same product
    bought from `cheaper_supplier`; a benchmark or marketplace one is priced at `price_ratio` of
    the item's unit price. `origin` adds what the source says of it, and `verdicts` overrides
    an attribute's comparison verdict, with its reason."""

    supplier: str
    product: str
    source: str
    match: str
    cheaper_supplier: str | None = None
    price_ratio: str | None = None
    name: str | None = None
    origin: dict = field(default_factory=dict)
    verdicts: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    found_days_ago: int = 3
