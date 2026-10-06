"""A framework agreement the demo company signed, with its terms and the PDF's text."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class TermSpec:
    """One confirmed term. `products` are the product keys whose lines are in its scope, from any
    supplier; `quote` is the clause it was read from, on `page` of the PDF."""

    key: str
    kind: str
    scope: str
    products: tuple[str, ...]
    leaves: tuple[str, ...]
    quote: str
    page: int
    item: str | None = None
    unit: str | None = None
    unit_price: Decimal | None = None
    discount_percent: Decimal | None = None
    commitment_amount: Decimal | None = None
    commitment_period: str | None = None
    tiers: tuple[dict, ...] = ()
    confidence: Decimal = Decimal("0.94")


@dataclass(frozen=True)
class AgreementSpec:
    """`pages` is the PDF's text, a list of lines per page."""

    key: str
    title: str
    reference: str
    supplier: str
    starts_on: date
    ends_on: date
    summary: str
    filename: str
    uploaded_on: date
    terms: tuple[TermSpec, ...]
    pages: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
